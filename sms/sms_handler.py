"""SMS command checking and handling."""
import json
from tools.tool_executor import call_termux
from storage import STATE_FILE, save_json, load_json
from memory import lookup_contact

MAX_NOTIFICATION_LENGTH = 100


def check_for_sms_commands(state, config):
    """Check for new SMS commands from the user."""
    raw_sms = call_termux("termux-sms-list -l 20")
    if not raw_sms or raw_sms == "[]":
        return None

    try:
        sms_list = json.loads(raw_sms)
        sms_list = sorted(sms_list, key=lambda msg: int(msg.get("_id", 0)))
        for msg in sms_list:
            phone_number = config["user"]["phone_number"]
            sender_number = msg.get("number", "")
            is_from_user = sender_number.replace(" ", "").endswith(phone_number[-8:])
            is_inbox = msg.get("type") == "inbox"

            if is_inbox:
                current_id = int(msg.get("_id"))
                if current_id > state["last_checked_sms_id"]:
                    state["last_checked_sms_id"] = current_id
                    save_json(STATE_FILE, state)
                    
                    if is_from_user:
                        # Message from owner - process as command
                        return msg.get("body")
                    else:
                        # Message from someone else - notify owner
                        notify_owner_of_sms(sender_number, msg.get("body", ""), config)
    except Exception as e:
        print(f"SMS Error: {e}")
    return None


def notify_owner_of_sms(sender_number, message_body, config):
    """Notify the owner about an SMS from someone else."""
    contact = lookup_contact(sender_number, config)
    
    if contact:
        sender_info = contact.get("name", sender_number)
        relationship = contact.get("relationship", "")
        if relationship:
            sender_info = f"{sender_info} ({relationship})"
    else:
        sender_info = sender_number
    
    notification = f"📩 Ny SMS fra {sender_info}: {message_body[:MAX_NOTIFICATION_LENGTH]}"
    if len(message_body) > MAX_NOTIFICATION_LENGTH:
        notification += "..."
    
    owner_number = config["user"]["phone_number"]
    call_termux(f'termux-sms-send -n {owner_number} "{notification}"')
    print(f"Varslet eier om SMS fra {sender_info}")
