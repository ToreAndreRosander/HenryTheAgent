"""Memory management agent for extracting and categorizing memories."""
import json
from datetime import datetime
from storage import MEMORY_FILE, load_json, save_json
from storage.file_manager import build_default_memory
from config import DEFAULT_CONFIG

DEFAULT_PHONE_NUMBER = DEFAULT_CONFIG["user"]["phone_number"]
DATE_FORMAT = "%Y-%m-%d"


def extract_memories_from_conversation(conversation_text, config=None):
    """
    Analyze conversation and extract important information to remember.
    This is designed to be called by an LLM separately.
    
    Returns a structured dict of memories to save.
    """
    # This function is meant to be called with LLM assistance
    # The LLM will analyze the text and return structured data
    return {
        "notes": [],
        "contacts": [],
        "short_term": {}
    }


def should_update_memory(conversation_history):
    """
    Determine if memory should be updated based on conversation context.
    
    Returns True if conversation contains information worth remembering:
    - New contacts mentioned
    - User's current location or activity
    - Future plans
    - Important facts about the user
    """
    # Simple heuristics - in a real implementation, this will use LLM at a later stage
    keywords = [
        "heter", "navn", "møte", "jobb", "på vei", "kommer til", 
        "planlegger", "skal", "husker", "kontakt", "telefon",
        "sønnen min", "kona mi", "sjefen", "venn"
    ]
    
    if not conversation_history:
        return False
    
    # Check recent messages
    recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    for entry in recent_messages:
        content = entry.get("content", "").lower()
        if any(keyword in content for keyword in keywords):
            return True
    
    return False


def process_memory_update(user_message, assistant_response, config=None):
    """
    Process a conversation turn and update memory if needed.
    This uses simple pattern matching - could be enhanced with LLM.
    """
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    
    updated = False
    message_lower = user_message.lower()
    
    # Extract current date if mentioned
    if "i dag" in message_lower or "i morgen" in message_lower:
        memory["short_term_memory"]["current_date"] = datetime.now().strftime(DATE_FORMAT)
        updated = True
    
    # Extract location/activity context
    location_patterns = [
        "er på jobb", "er hjemme", "er på", "er i", 
        "sitter på", "står på"
    ]
    for pattern in location_patterns:
        if pattern in message_lower:
            # Extract the location
            start_idx = message_lower.find(pattern)
            location_part = user_message[start_idx:start_idx+50]
            memory["short_term_memory"]["current_context"] = location_part
            updated = True
            break
    
    # Extract future plans
    future_patterns = ["skal", "kommer til å", "planlegger"]
    for pattern in future_patterns:
        if pattern in message_lower:
            memory["short_term_memory"]["today_plans"].append(user_message)
            updated = True
            break
    
    if updated:
        save_json(MEMORY_FILE, memory)
        return True
    
    return False


def get_memory_context_for_llm(config=None):
    """
    Get formatted memory context to include in LLM prompt.
    Combines contacts, notes, and short-term memory.
    """
    phone_number = config["user"]["phone_number"] if config else DEFAULT_PHONE_NUMBER
    memory = load_json(MEMORY_FILE, build_default_memory(phone_number))
    
    context_parts = []
    
    # Add contact information
    contacts = memory.get("contacts", [])
    if contacts:
        contact_info = []
        for contact in contacts:
            name = contact.get("name", "")
            relationship = contact.get("relationship", "")
            tone = contact.get("tone_preference", "normal")
            ctx = contact.get("context", "")
            
            info = f"{name}"
            if relationship:
                info += f" ({relationship})"
            if tone and tone != "normal":
                info += f" - tone: {tone}"
            if ctx:
                info += f" - {ctx}"
            contact_info.append(info)
        
        context_parts.append("KONTAKTER:\n" + "\n".join(contact_info))
    
    # Add short-term memory
    stm = memory.get("short_term_memory", {})
    if any(stm.values()):
        stm_info = []
        if stm.get("current_date"):
            stm_info.append(f"Dato: {stm['current_date']}")
        if stm.get("current_context"):
            stm_info.append(f"Kontekst: {stm['current_context']}")
        if stm.get("user_location"):
            stm_info.append(f"Sted: {stm['user_location']}")
        if stm.get("user_activity"):
            stm_info.append(f"Aktivitet: {stm['user_activity']}")
        if stm.get("today_plans"):
            stm_info.append(f"Planer: {', '.join(stm['today_plans'])}")
        
        if stm_info:
            context_parts.append("KORTTIDSMINNE:\n" + "\n".join(stm_info))
    
    # Add recent notes
    notes = memory.get("notes", [])
    if notes:
        recent_notes = notes[-5:]  # Last 5 notes
        note_texts = [n.get("note", "") for n in recent_notes]
        context_parts.append("VIKTIGE NOTATER:\n" + "\n".join(note_texts))
    
    return "\n\n".join(context_parts) if context_parts else ""
