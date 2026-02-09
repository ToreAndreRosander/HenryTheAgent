"""Onboarding flow for initial setup."""
import os
from datetime import datetime
from config import DEFAULT_CONFIG, merge_dicts
from storage import MEMORY_FILE, CONFIG_FILE, DATA_DIR, load_json, save_json
from storage.file_manager import build_default_memory


def check_termux_permissions():
    """Check Termux permissions and access."""
    results = []

    data_test_path = os.path.join(DATA_DIR, "permission_test.json")
    try:
        save_json(data_test_path, {"timestamp": datetime.utcnow().isoformat()})
        os.remove(data_test_path)
        results.append(("Skrive datafil", True, f"OK: {DATA_DIR}"))
    except Exception as exc:
        results.append(("Skrive datafil", False, f"Feil: {exc}"))

    storage_path = os.path.expanduser("~/storage/downloads")
    if not os.path.exists(storage_path):
        results.append(("Termux storage", False, "Fant ikke ~/storage/downloads. Kjør termux-setup-storage."))
    else:
        storage_test_path = os.path.join(storage_path, "permission_test.txt")
        try:
            with open(storage_test_path, "w", encoding="utf-8") as handle:
                handle.write("termux permission test")
            os.remove(storage_test_path)
            results.append(("Skrive til storage", True, f"OK: {storage_path}"))
        except Exception as exc:
            results.append(("Skrive til storage", False, f"Feil: {exc}"))

    return results


def prompt_choice(prompt, options, default=None):
    """Prompt user for a choice from a list of options."""
    options_display = "/".join(options)
    while True:
        raw = input(f"{prompt} ({options_display}){f' [{default}]' if default else ''}: ").strip().lower()
        if not raw and default:
            return default
        if raw in options:
            return raw
        print("Ugyldig valg. Prøv igjen.")


def prompt_text(prompt, default=None):
    """Prompt user for text input."""
    raw = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return raw or default


def run_onboarding_flow(config):
    """Run the onboarding flow to configure the agent."""
    print("Starter onboarding...")
    config = merge_dicts(DEFAULT_CONFIG, config)

    phone_number = prompt_text("Telefonnummer som agenten skal bruke", config["user"]["phone_number"])
    if phone_number:
        config["user"]["phone_number"] = phone_number

    mode = prompt_choice("Velg LLM-oppsett", ["http", "mqtt"], config["llm"]["mode"])
    config["llm"]["mode"] = mode

    if mode == "http":
        config["llm"]["http"]["server_url"] = prompt_text(
            "HTTP server URL",
            config["llm"]["http"]["server_url"]
        )
        config["llm"]["http"]["model_name"] = prompt_text(
            "Model navn",
            config["llm"]["http"]["model_name"]
        )
    else:
        config["llm"]["mqtt"]["broker"] = prompt_text(
            "MQTT broker",
            config["llm"]["mqtt"]["broker"]
        )
        port = prompt_text("MQTT port", str(config["llm"]["mqtt"]["port"]))
        if port and port.isdigit():
            config["llm"]["mqtt"]["port"] = int(port)
        timeout = prompt_text("MQTT timeout (sek)", str(config["llm"]["mqtt"]["timeout"]))
        if timeout and timeout.isdigit():
            config["llm"]["mqtt"]["timeout"] = int(timeout)
        config["llm"]["mqtt"]["request_topic"] = prompt_text(
            "MQTT request topic",
            config["llm"]["mqtt"]["request_topic"]
        )
        config["llm"]["mqtt"]["response_topic_template"] = prompt_text(
            "MQTT response topic template (bruk {request_id})",
            config["llm"]["mqtt"]["response_topic_template"]
        )

    if prompt_choice("Kjør Termux rettighetstest", ["ja", "nei"], "ja") == "ja":
        results = check_termux_permissions()
        print("Rettighetstest:")
        for name, ok, detail in results:
            status = "OK" if ok else "FEIL"
            print(f"- {name}: {status} ({detail})")

    if prompt_choice("Ønsker du å svare på onboarding-spørsmål", ["ja", "nei"], "ja") == "ja":
        memory = load_json(MEMORY_FILE, build_default_memory(config["user"]["phone_number"]))
        memory.setdefault("profile", {})
        memory.setdefault("preferences", {})

        name = prompt_text("Hva heter du?", memory["profile"].get("name"))
        if name:
            memory["profile"]["name"] = name

        age = prompt_text("Hvor gammel er du?", str(memory["profile"].get("age", "")))
        if age and age.isdigit():
            memory["profile"]["age"] = int(age)

        bio = prompt_text("Kort bio", memory["profile"].get("bio"))
        if bio:
            memory["profile"]["bio"] = bio

        locale = prompt_text("Språk/locale", memory["profile"].get("locale"))
        if locale:
            memory["profile"]["locale"] = locale

        tone = prompt_text("Ønsket tone", memory["preferences"].get("tone"))
        if tone:
            memory["preferences"]["tone"] = tone

        response_style = prompt_text("Svarstil", memory["preferences"].get("response_style"))
        if response_style:
            memory["preferences"]["response_style"] = response_style

        interests = prompt_text("Interesser (kommaseparert)", ", ".join(memory.get("interests", [])))
        if interests is not None:
            memory["interests"] = [item.strip() for item in interests.split(",") if item.strip()]

        note = prompt_text("Ekstra notat (valgfritt)", "")
        if note:
            memory.setdefault("notes", []).append({
                "note": note,
                "timestamp": datetime.utcnow().isoformat()
            })

        save_json(MEMORY_FILE, memory)

    config["onboarding"]["completed"] = True
    save_json(CONFIG_FILE, config)
    print("Onboarding fullført.")
    return config
