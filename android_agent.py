"""
Android Agent - Main entry point
Modular structure for easier maintenance and extension.
"""
import argparse
import json
import time
from config import load_config
from storage import STATE_FILE, DEFAULT_STATE, ensure_data_files, load_json, save_json
from tasks import run_scheduled_tasks
from llm import process_llm_task
from sms import check_for_sms_commands
from onboarding import run_onboarding_flow
from tools.tool_executor import call_termux


def run_agent_loop(config):
    """Main agent loop that checks for SMS and processes tasks."""
    ensure_data_files(config)
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
        instruction = check_for_sms_commands(state, config)

        if instruction:
            print(f"PROSESSERER: {instruction}")
            process_llm_task(instruction, config)

        time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Termux Android agent")
    parser.add_argument("--onboarding", action="store_true", help="Kjør onboarding og konfigurer agenten")
    args = parser.parse_args()

    CURRENT_CONFIG = load_config()
    if args.onboarding:
        CURRENT_CONFIG = run_onboarding_flow(CURRENT_CONFIG)
    run_agent_loop(CURRENT_CONFIG)
