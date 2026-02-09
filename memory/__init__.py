"""Memory and history management."""
from .memory_manager import (
    append_history,
    get_history_context,
    update_memory,
    lookup_contact,
    add_or_update_contact,
    update_short_term_memory,
    get_short_term_memory,
    MAX_HISTORY_ITEMS
)
from .memory_agent import (
    process_memory_update,
    get_memory_context_for_llm,
    should_update_memory
)

__all__ = [
    "append_history",
    "get_history_context",
    "update_memory",
    "lookup_contact",
    "add_or_update_contact",
    "update_short_term_memory",
    "get_short_term_memory",
    "process_memory_update",
    "get_memory_context_for_llm",
    "should_update_memory",
    "MAX_HISTORY_ITEMS"
]
