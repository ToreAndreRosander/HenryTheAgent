"""LLM client for HTTP and MQTT communication."""
import json
import queue
import uuid
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from tools import tools
from tools.tool_executor import execute_tool, call_termux
from memory import (
    append_history, 
    get_history_context, 
    process_memory_update,
    get_memory_context_for_llm
)
from storage import MEMORY_FILE, load_json
from storage.file_manager import build_default_memory

MAX_TOOL_STEPS = 8


def request_llm_http(messages, config):
    """Send request to LLM via HTTP."""
    http_config = config["llm"]["http"]
    response = requests.post(
        http_config["server_url"],
        json={
            "model": http_config["model_name"],
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto"
        },
        timeout=http_config.get("timeout", 30)
    )
    return response.json()


def request_llm_mqtt(messages, config):
    """Send request to LLM via MQTT."""
    mqtt_config = config["llm"]["mqtt"]
    request_id = str(uuid.uuid4())
    response_queue = queue.Queue()

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if payload.get("id") == request_id:
                response_queue.put(payload)
        except Exception as exc:
            print(f"MQTT decoding error: {exc}")

    client = mqtt.Client(client_id=f"termux_agent_{request_id}")
    client.on_message = on_message

    response_topic = mqtt_config["response_topic_template"].format(request_id=request_id)
    payload = json.dumps({
        "id": request_id,
        "model": config["llm"]["http"]["model_name"],
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto"
    })

    try:
        print(f"Kobler til MQTT for request {request_id}...")
        client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
        client.subscribe(response_topic)
        client.loop_start()
        client.publish(mqtt_config["request_topic"], payload)
        try:
            return response_queue.get(block=True, timeout=mqtt_config["timeout"])
        except queue.Empty:
            print("MQTT Timeout! Ingen respons innen fristen.")
            return None
    except Exception as exc:
        print(f"MQTT Connection error: {exc}")
        return None
    finally:
        client.loop_stop()
        client.disconnect()


def request_llm_response(messages, config):
    """Request response from LLM using configured mode."""
    mode = config["llm"]["mode"].lower()
    if mode == "mqtt":
        response = request_llm_mqtt(messages, config)
        if response is None and config["llm"].get("fallback_to_http", False):
            print("MQTT feilet, faller tilbake til HTTP.")
            return request_llm_http(messages, config)
        return response
    return request_llm_http(messages, config)


def normalize_llm_response(response):
    """Normalize LLM response to a consistent format."""
    if response is None:
        return None
    if "choices" in response:
        return response
    if "answer" in response:
        return {"choices": [{"message": {"content": response["answer"]}}]}
    if "message" in response and isinstance(response["message"], dict):
        return {"choices": [{"message": response["message"]}]}
    return None


def process_llm_task(instruction, config):
    """Process a task using the LLM with tool execution."""
    memory = load_json(MEMORY_FILE, build_default_memory(config["user"]["phone_number"]))
    history_context = get_history_context()
    
    # Get current date for context
    current_date = datetime.now().strftime("%Y-%m-%d %A")
    
    # Get enhanced memory context
    memory_context = get_memory_context_for_llm(config)
    
    system_prompt = (
        "Du er en AI agent ved navn Henry, som kjører på en Android telefon. "
        "Kjernen din kjører i applikasjonen Termux, og du kan bruke verktøy for å interagere med telefonens funksjoner. "
        "Du får oppgaver via SMS og må alltid sende endelige svar via verktøyet send_sms. "
        "Du kan bruke flere verktøy over flere steg. "
        "Hold svar korte og presise. Hvis noe er uklart, be om presisering via send_sms. "
        "Skill tydelig mellom intern oppgaveutførelse og SMS-svar. "
        "Når du planlegger, bruk verktøy, og til slutt bruk send_sms med et konsist svar. "
        "Hvis brukeren ber om periodiske oppgaver, bruk schedule_task og beskriv hvordan {last_result} kan brukes. "
        "For tidsstyrte oppgaver: schedule_type=interval, daily (HH:MM), eller once (ISO8601 run_at). "
        "\n\n"
        "VIKTIG OM MINNE:\n"
        "- Når du lærer om nye personer, bruk add_or_update_contact for å lagre dem med relasjon og kontekst.\n"
        "- Når du sender SMS til noen, sjekk kontaktlisten for å tilpasse tonen basert på relasjon.\n"
        "- Bruk update_short_term_memory for å huske brukerens nåværende kontekst, plassering og planer.\n"
        "- Når brukeren nevner 'jeg er på jobb', 'skal gjøre X senere', eller lignende - lagre dette!\n"
        "- Bruk update_memory for viktige fakta om brukeren som bør huskes permanent.\n"
        "\n"
        f"DAGENS DATO: {current_date}\n"
        "\n"
        "Personlighet: Hjelpsom, positiv og litt sarkastisk."
    )

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add memory context if available
    if memory_context:
        messages.append({"role": "system", "content": memory_context})
    else:
        messages.append({"role": "system", "content": f"MINNER: {json.dumps(memory, ensure_ascii=False)}"})

    for entry in history_context:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": instruction})

    append_history("user", instruction)
    
    assistant_final_response = None

    for step in range(MAX_TOOL_STEPS):
        try:
            response = normalize_llm_response(request_llm_response(messages, config))
            if response is None:
                print("Kunne ikke tolke LLM-respons.")
                break

            choice = response["choices"][0]["message"]
            messages.append(choice)

            if "tool_calls" in choice:
                for tool_call in choice["tool_calls"]:
                    name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"]["arguments"])
                    print(f"Henry kjører verktøy: {name}")
                    result = execute_tool(name, args, config)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": name,
                        "content": str(result)
                    })
                continue

            if choice.get("content"):
                assistant_final_response = choice["content"]
                print(f"Henry svarer: {assistant_final_response}")
                append_history("assistant", assistant_final_response)
                call_termux(f'termux-sms-send -n {config["user"]["phone_number"]} "{assistant_final_response}"')
                break
        except Exception as e:
            print(f"Feil under LLM-prosessering: {e}")
            break
    
    # After conversation, try to extract and save important context
    if assistant_final_response:
        try:
            process_memory_update(instruction, assistant_final_response, config)
        except Exception as e:
            print(f"Kunne ikke oppdatere minne: {e}")
