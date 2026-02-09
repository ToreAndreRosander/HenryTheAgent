"""Memory and history management."""
from datetime import datetime
from storage import HISTORY_FILE, MEMORY_FILE, load_json, save_json
from storage.file_manager import build_default_memory
from config import DEFAULT_CONFIG

MAX_HISTORY_ITEMS = 30
DEFAULT_PHONE_NUMBER = DEFAULT_CONFIG["user"]["phone_number"]


def append_history(role, content):
    """Append a message to the conversation history."""
    history = load_json(HISTORY_FILE, [])
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    history = history[-MAX_HISTORY_ITEMS:]
    save_json(HISTORY_FILE, history)


def get_history_context():
    """Get recent conversation history for context."""
    history = load_json(HISTORY_FILE, [])
    return history[-12:]


def update_memory(args, config=None):
    """Update user memory with a new note."""
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    note = args.get("note", "").strip()
    if not note:
        return "Ingen notat oppgitt"
    memory.setdefault("notes", []).append({
        "note": note,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_json(MEMORY_FILE, memory)
    return "Minne lagret"


def lookup_contact(phone_number, config=None):
    """Look up a contact by phone number."""
    phone_number_clean = phone_number.replace(" ", "").replace("+", "")
    owner_phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(owner_phone_number))
    
    contacts = memory.get("contacts", [])
    for contact in contacts:
        contact_number = contact.get("number", "").replace(" ", "").replace("+", "")
        if contact_number in phone_number_clean or phone_number_clean in contact_number:
            return contact
    return None


def add_or_update_contact(args, config=None):
    """Add or update a contact in memory."""
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    
    contact_number = args.get("number", "").strip()
    if not contact_number:
        return "Telefonnummer mangler"
    
    name = args.get("name", "")
    relationship = args.get("relationship", "")
    tone_preference = args.get("tone_preference", "normal")
    context = args.get("context", "")
    
    contacts = memory.setdefault("contacts", [])
    
    # Check if contact already exists
    contact_number_clean = contact_number.replace(" ", "").replace("+", "")
    for i, contact in enumerate(contacts):
        existing_number = contact.get("number", "").replace(" ", "").replace("+", "")
        if existing_number == contact_number_clean:
            # Update existing contact
            if name:
                contacts[i]["name"] = name
            if relationship:
                contacts[i]["relationship"] = relationship
            if tone_preference:
                contacts[i]["tone_preference"] = tone_preference
            if context:
                contacts[i]["context"] = context
            save_json(MEMORY_FILE, memory)
            return f"Kontakt {name or contact_number} oppdatert"
    
    # Add new contact
    new_contact = {
        "name": name or contact_number,
        "number": contact_number,
        "relationship": relationship,
        "tone_preference": tone_preference,
        "context": context
    }
    contacts.append(new_contact)
    save_json(MEMORY_FILE, memory)
    return f"Kontakt {name or contact_number} lagt til"


def update_short_term_memory(args, config=None):
    """Update short-term memory with current context."""
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    
    stm = memory.setdefault("short_term_memory", {
        "current_context": "",
        "current_date": "",
        "user_location": "",
        "user_activity": "",
        "today_plans": []
    })
    
    if "context" in args:
        stm["current_context"] = args["context"]
    if "date" in args:
        stm["current_date"] = args["date"]
    if "location" in args:
        stm["user_location"] = args["location"]
    if "activity" in args:
        stm["user_activity"] = args["activity"]
    if "plan" in args:
        plan = args["plan"]
        if plan not in stm["today_plans"]:
            stm["today_plans"].append(plan)
    
    save_json(MEMORY_FILE, memory)
    return "Korttidsminne oppdatert"


def get_short_term_memory(config=None):
    """Retrieve short-term memory."""
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    return memory.get("short_term_memory", {})
