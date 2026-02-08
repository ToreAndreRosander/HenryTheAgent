import os
import requests
import subprocess
import json
import time
from datetime import datetime, timedelta

# --- KONFIGURASJON ---
SERVER_URL = "http://local-llama-cpp:5034/v1/chat/completions"
MODEL_NAME = "qwen2.5"
MY_NUMBER = "ditt-nummer-her"  # Erstatt med ditt telefonnummer, eksludert landskode, for å identifisere innkommende SMS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
MEMORY_FILE = os.path.join(DATA_DIR, "user_profile.json")

MAX_HISTORY_ITEMS = 30
MAX_TOOL_STEPS = 8

AGENT_HARDWARE = "generisk Android"  # Endre til spesifikk modell hvis ønskelig, eller la det være generisk

DEFAULT_MEMORY = {
    "profile": {
        "name": "Ditt navn",
        "age": 99,
        "bio": "Kort beskrivelse av deg selv",
        "locale": "no-NO"
    },
    "contacts": [
        {
            "name": "Ditt navn",
            "number": MY_NUMBER,
            "relationship": "Eier"
        }
    ],
    "preferences": {
        "tone": "Hjelpsom, positiv og litt sarkastisk",
        "response_style": "kort og presist via SMS"
    },
    "interests": ["teknologi", "programmering"],
    "notes": []
}

DEFAULT_STATE = {
    "last_checked_sms_id": 0
}

def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MEMORY_FILE):
        save_json(MEMORY_FILE, DEFAULT_MEMORY)
    if not os.path.exists(STATE_FILE):
        save_json(STATE_FILE, DEFAULT_STATE)
    if not os.path.exists(HISTORY_FILE):
        save_json(HISTORY_FILE, [])
    if not os.path.exists(TASKS_FILE):
        save_json(TASKS_FILE, [])


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def save_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def call_termux(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

def execute_tool(name, args):
    if name == "get_battery_status":
        return call_termux("termux-battery-status")
    if name == "get_wifi_info":
        return call_termux("termux-wifi-connectioninfo")
    if name == "get_location":
        return call_termux("termux-location")
    if name == "get_device_info":
        return call_termux("termux-telephony-deviceinfo")
    if name == "get_clipboard":
        return call_termux("termux-clipboard-get")
    if name == "set_clipboard":
        value = args.get("text", "")
        call_termux(f"termux-clipboard-set '{value}'")
        return "Clipboard oppdatert"
    if name == "send_sms":
        num = args.get("number") or MY_NUMBER
        msg = args.get("message", "")
        call_termux(f'termux-sms-send -n {num} "{msg}"')
        return f"SMS sendt til {num}"
    if name == "send_mms":
        num = args.get("number") or MY_NUMBER
        filepath = args.get("file_path")
        msg = args.get("message", "")
        if filepath:
            call_termux(f'termux-sms-send -n {num} -a "{filepath}" "{msg}"')
            return f"MMS sendt til {num}: {filepath}"
        return "MMS feilet: mangler filsti"
    if name == "take_photo":
        filename = f"photo_{int(time.time())}.jpg"
        target = os.path.expanduser(f"~/storage/downloads/{filename}")
        call_termux(f"termux-camera-photo -c 0 '{target}'")
        return target
    if name == "list_files":
        path = args.get("path", "~/storage")
        return call_termux(f"ls -al {path}")
    if name == "read_file":
        path = args.get("path", "")
        if not path:
            return "Mangler filsti"
        return call_termux(f"sed -n '1,200p' {path}")
    if name == "schedule_task":
        return schedule_task(args)
    if name == "list_tasks":
        return list_tasks()
    if name == "cancel_task":
        return cancel_task(args)
    if name == "update_memory":
        return update_memory(args)
    return "Ukjent verktøy"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Henter batteristatus",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wifi_info",
            "description": "Henter info om WiFi-tilkobling",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location",
            "description": "Henter GPS-posisjon",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_info",
            "description": "Henter telephony/device info",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Leser utklippstavlen",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Setter utklippstavlen",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Tekst til utklippstavlen"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_sms",
            "description": "Sender en SMS til et spesifisert nummer. Bruk dette for alle endelige svar til brukeren.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Mottakerens telefonnummer"},
                    "message": {"type": "string", "description": "Meldingstekst"}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_mms",
            "description": "Sender MMS med vedlegg",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Mottakerens telefonnummer"},
                    "message": {"type": "string", "description": "Meldingstekst"},
                    "file_path": {"type": "string", "description": "Filsti til vedlegg"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_photo",
            "description": "Tar et bilde med telefonens kamera (bakside som standard)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lister filer i en mappe",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Mappe å liste"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Leser de første linjene i en fil",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Filsti"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Planlegger en oppgave. schedule_type: interval, daily, once. For daily bruk daily_time (HH:MM). For once bruk run_at (ISO8601). actions er en liste med tool_name og tool_args. Bruk {last_result} for å referere til forrige verktøyresultat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Navn på oppgaven"},
                    "interval_minutes": {"type": "integer", "description": "Hvor ofte i minutter"},
                    "schedule_type": {"type": "string", "description": "interval, daily, once"},
                    "daily_time": {"type": "string", "description": "HH:MM for daglige oppgaver"},
                    "run_at": {"type": "string", "description": "ISO8601 tidspunkt for engangsoppgaver"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_name": {"type": "string"},
                                "tool_args": {"type": "object"}
                            },
                            "required": ["tool_name"]
                        }
                    }
                },
                "required": ["name", "actions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Lister planlagte oppgaver",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_task",
            "description": "Deaktiverer en planlagt oppgave",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID på oppgaven"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": "Lagrer et minne i user_profile.json",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "Hva som skal lagres"}
                },
                "required": ["note"]
            }
        }
    }
]

def append_history(role, content):
    history = load_json(HISTORY_FILE, [])
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    history = history[-MAX_HISTORY_ITEMS:]
    save_json(HISTORY_FILE, history)


def get_history_context():
    history = load_json(HISTORY_FILE, [])
    return history[-12:]


def update_memory(args):
    memory = load_json(MEMORY_FILE, DEFAULT_MEMORY)
    note = args.get("note", "").strip()
    if not note:
        return "Ingen notat oppgitt"
    memory.setdefault("notes", []).append({
        "note": note,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_json(MEMORY_FILE, memory)
    return "Minne lagret"


def schedule_task(args):
    tasks = load_json(TASKS_FILE, [])
    task_id = f"task_{int(time.time())}"
    schedule_type = args.get("schedule_type", "interval")
    now = datetime.utcnow()
    task = {
        "id": task_id,
        "name": args.get("name", task_id),
        "schedule_type": schedule_type,
        "interval_minutes": args.get("interval_minutes"),
        "daily_time": args.get("daily_time"),
        "run_at": args.get("run_at"),
        "actions": args.get("actions", []),
        "last_run": None,
        "next_run": None,
        "enabled": True
    }

    if schedule_type == "interval":
        interval_minutes = int(args.get("interval_minutes", 0))
        if interval_minutes <= 0:
            return "Ugyldig intervall"
        task["interval_minutes"] = interval_minutes
        task["next_run"] = (now + timedelta(minutes=interval_minutes)).isoformat()
    elif schedule_type == "daily":
        daily_time = args.get("daily_time")
        if not daily_time or len(daily_time.split(":")) != 2:
            return "Ugyldig tidspunkt for daily (HH:MM)"
        hour, minute = daily_time.split(":")
        next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        task["daily_time"] = daily_time
        task["next_run"] = next_run.isoformat()
    elif schedule_type == "once":
        run_at = args.get("run_at")
        if not run_at:
            return "Ugyldig tidspunkt for once (ISO8601)"
        try:
            next_run = datetime.fromisoformat(run_at)
        except ValueError:
            return "Ugyldig tidspunkt for once (ISO8601)"
        task["run_at"] = run_at
        task["next_run"] = next_run.isoformat()
    else:
        return "Ugyldig schedule_type"

    tasks.append(task)
    save_json(TASKS_FILE, tasks)
    return f"Oppgave planlagt: {task_id}"


def list_tasks():
    tasks = load_json(TASKS_FILE, [])
    return json.dumps(tasks, ensure_ascii=False, indent=2)


def cancel_task(args):
    task_id = args.get("task_id")
    tasks = load_json(TASKS_FILE, [])
    updated = False
    for task in tasks:
        if task.get("id") == task_id:
            task["enabled"] = False
            updated = True
    save_json(TASKS_FILE, tasks)
    return "Oppgave deaktivert" if updated else "Fant ikke oppgave"


def run_scheduled_tasks():
    tasks = load_json(TASKS_FILE, [])
    now = datetime.utcnow()
    changed = False

    for task in tasks:
        if not task.get("enabled", True):
            continue
        next_run = task.get("next_run")
        if not next_run:
            continue
        if datetime.fromisoformat(next_run) > now:
            continue

        last_result = ""
        for action in task.get("actions", []):
            tool_name = action.get("tool_name")
            tool_args = action.get("tool_args", {})
            resolved_args = {}
            for key, value in tool_args.items():
                if isinstance(value, str):
                    resolved_args[key] = value.replace("{last_result}", last_result)
                else:
                    resolved_args[key] = value
            last_result = execute_tool(tool_name, resolved_args)

        task["last_run"] = now.isoformat()
        schedule_type = task.get("schedule_type", "interval")
        if schedule_type == "interval":
            interval_minutes = int(task.get("interval_minutes", 0))
            task["next_run"] = (now + timedelta(minutes=interval_minutes)).isoformat()
        elif schedule_type == "daily":
            daily_time = task.get("daily_time", "06:00")
            hour, minute = daily_time.split(":")
            next_run_dt = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if next_run_dt <= now:
                next_run_dt += timedelta(days=1)
            task["next_run"] = next_run_dt.isoformat()
        elif schedule_type == "once":
            task["enabled"] = False
        else:
            task["enabled"] = False
        changed = True

    if changed:
        save_json(TASKS_FILE, tasks)

def process_llm_task(instruction):
    memory = load_json(MEMORY_FILE, DEFAULT_MEMORY)
    history_context = get_history_context()
    system_prompt = (
        "Du er en AI agent ved navn Henry. Maskinvaren din er en {AGENT_HARDWARE}. "
        "Kjernen din kjører i applikasjonen Termux, og du kan bruke verktøy for å interagere med telefonens funksjoner. "
        "Du får oppgaver via SMS og må alltid sende endelige svar via verktøyet send_sms. "
        "Du kan bruke flere verktøy over flere steg. "
        "Hold svar korte og presise. Hvis noe er uklart, be om presisering via send_sms. "
        "Skill tydelig mellom intern oppgaveutførelse og SMS-svar. "
        "Når du planlegger, bruk verktøy, og til slutt bruk send_sms med et konsist svar. "
        "Hvis brukeren ber om periodiske oppgaver, bruk schedule_task og beskriv hvordan {last_result} kan brukes. "
        "For tidsstyrte oppgaver: schedule_type=interval, daily (HH:MM), eller once (ISO8601 run_at). "
        "Personlighet: Hjelpsom, positiv og litt sarkastisk."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "system", "content": f"MINNER: {json.dumps(memory, ensure_ascii=False)}"})

    for entry in history_context:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": instruction})

    append_history("user", instruction)

    for step in range(MAX_TOOL_STEPS):
        try:
            response = requests.post(
                SERVER_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                },
                timeout=30
            ).json()

            choice = response["choices"][0]["message"]
            messages.append(choice)

            if "tool_calls" in choice:
                for tool_call in choice["tool_calls"]:
                    name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"]["arguments"])
                    print(f"Henry kjører verktøy: {name}")
                    result = execute_tool(name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": name,
                        "content": str(result)
                    })
                continue

            if choice.get("content"):
                print(f"Henry svarer: {choice['content']}")
                append_history("assistant", choice["content"])
                call_termux(f'termux-sms-send -n {MY_NUMBER} "{choice["content"]}"')
                break
        except Exception as e:
            print(f"Feil under LLM-prosessering: {e}")
            break


def check_for_sms_commands(state):
    raw_sms = call_termux("termux-sms-list -l 20")
    if not raw_sms or raw_sms == "[]":
        return None

    try:
        sms_list = json.loads(raw_sms)
        sms_list = sorted(sms_list, key=lambda msg: int(msg.get("_id", 0)))
        for msg in sms_list:
            is_from_user = msg.get("number", "").replace(" ", "").endswith(MY_NUMBER[-8:])
            is_inbox = msg.get("type") == "inbox"

            if is_from_user and is_inbox:
                current_id = int(msg.get("_id"))
                if current_id > state["last_checked_sms_id"]:
                    state["last_checked_sms_id"] = current_id
                    save_json(STATE_FILE, state)
                    return msg.get("body")
    except Exception as e:
        print(f"SMS Error: {e}")
    return None


def run_agent_loop():
    ensure_data_files()
    state = load_json(STATE_FILE, DEFAULT_STATE)
    print("Henry våkner... Nullstiller innboks for å ignorere gamle meldinger.")

    try:
        data = json.loads(call_termux("termux-sms-list -l 20"))
        inbox_ids = [int(m["_id"]) for m in data if m.get("type") == "inbox"]
        if inbox_ids:
            state["last_checked_sms_id"] = max(inbox_ids)
        else:
            state["last_checked_sms_id"] = 0
        save_json(STATE_FILE, state)
        print(f"Synkronisert. Ignorerer alt med ID {state['last_checked_sms_id']} eller lavere.")
    except Exception as e:
        print(f"Kunne ikke synkronisere: {e}")
        state["last_checked_sms_id"] = 999999999
        save_json(STATE_FILE, state)

    while True:
        run_scheduled_tasks()
        instruction = check_for_sms_commands(state)

        if instruction:
            print(f"PROSESSERER: {instruction}")
            process_llm_task(instruction)

        time.sleep(5)

if __name__ == "__main__":
    run_agent_loop()
