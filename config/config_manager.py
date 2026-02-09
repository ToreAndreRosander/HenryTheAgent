"""Configuration loading and merging."""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "llm": {
        "mode": "http",
        "fallback_to_http": True,
        "http": {
            "server_url": "http://<url/ip>:<port>/v1/chat/completions",
            "model_name": "qwen2.5",
            "timeout": 30
        },
        "mqtt": {
            "broker": "<url/ip>",
            "port": 1883,
            "timeout": 45,
            "request_topic": "inference/request",
            "response_topic_template": "inference/response/{request_id}"
        }
    },
    "user": {
        "phone_number": ""
    },
    "onboarding": {
        "completed": False
    }
}


def merge_dicts(base, updates):
    """Recursively merge two dictionaries."""
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config():
    """Load configuration from file or return defaults."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return merge_dicts(DEFAULT_CONFIG, data)
    except Exception:
        return DEFAULT_CONFIG
