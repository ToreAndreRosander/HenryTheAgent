"""File I/O operations for data persistence."""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
MEMORY_FILE = os.path.join(DATA_DIR, "user_profile.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

DEFAULT_STATE = {
    "last_checked_sms_id": 0
}


def build_default_memory(phone_number):
    """Build default memory structure."""
    return {
        "profile": {
            "name": "",
            "age": 99,
            "bio": "",
            "locale": "no-NO"
        },
        "contacts": [
            {
                "name": "",
                "number": phone_number,
                "relationship": "Eier",
                "tone_preference": "normal",
                "context": "Dette er eieren av enheten"
            }
        ],
        "preferences": {
            "tone": "Hjelpsom, positiv og litt sarkastisk",
            "response_style": "kort og presist via SMS"
        },
        "interests": [""],
        "notes": [],
        "short_term_memory": {
            "current_context": "",
            "current_date": "",
            "user_location": "",
            "user_activity": "",
            "today_plans": []
        }
    }


def load_json(path, default):
    """Load JSON from file with fallback to default."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def save_json(path, payload):
    """Save JSON to file."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_data_files(config):
    """Ensure all required data files exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, config)
    if not os.path.exists(MEMORY_FILE):
        save_json(MEMORY_FILE, build_default_memory(config["user"]["phone_number"]))
    if not os.path.exists(STATE_FILE):
        save_json(STATE_FILE, DEFAULT_STATE)
    if not os.path.exists(HISTORY_FILE):
        save_json(HISTORY_FILE, [])
    if not os.path.exists(TASKS_FILE):
        save_json(TASKS_FILE, [])
