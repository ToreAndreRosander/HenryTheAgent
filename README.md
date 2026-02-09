# HenryTheAgent

## Overview
Meet Henry, a minimal python agent application that runs on an Android phone using Termux. It's an AI-powered assistant that responds to SMS commands and can execute various tasks using the phone's capabilities.

It's intended for a local LLM, and my current model is a Qwen2.5 14B hosted on a local llama.cpp server. It supports both http calls and MQTT (easier to communicate with localy hosted LLMs from the outside network). It should be possible to use other OpenAI basead endpoints.

The agent manages it's own short term and long term memory, and can store your relation to contacts, so it tailors it's tone of voice and responsee to external contacts.

NOTE: The agent will be able to send outgoing SMS, so use it wisely. You should run this agent on a separate device.
It's not intended for any types of production use, and should be considered as pre-alpha.

## Directory Structure

```
termux-agent/
├── android_agent.py          # Main entry point
├── config/                   # Configuration management
│   ├── __init__.py
│   └── config_manager.py     # Config loading and merging
├── storage/                  # Data persistence
│   ├── __init__.py
│   └── file_manager.py       # JSON file I/O operations
├── tools/                    # Tool execution
│   ├── __init__.py
│   ├── tool_definitions.py   # Tool schemas and descriptions
│   └── tool_executor.py      # Tool execution logic
├── llm/                      # LLM integration
│   ├── __init__.py
│   └── llm_client.py         # HTTP and MQTT client for LLM
├── tasks/                    # Task scheduling
│   ├── __init__.py
│   └── task_scheduler.py     # Scheduling and execution logic
├── memory/                   # Memory and history
│   ├── __init__.py
│   └── memory_manager.py     # Conversation history and user memory
├── sms/                      # SMS handling
│   ├── __init__.py
│   └── sms_handler.py        # SMS command checking
├── onboarding/               # Setup flow
│   ├── __init__.py
│   └── onboarding_flow.py    # Initial configuration wizard
└── data/                     # Runtime data
    ├── config.json
    ├── state.json
    ├── history.json
    ├── tasks.json
    └── user_profile.json
```

## Module Responsibilities

### config/
Manages application configuration including LLM settings, user preferences, and onboarding status.
- `DEFAULT_CONFIG`: Default configuration template
- `load_config()`: Load configuration from file or defaults
- `merge_dicts()`: Recursive dictionary merging

### storage/
Handles all file I/O operations for persistent data storage.
- `load_json()`: Load JSON with fallback to defaults
- `save_json()`: Save data as JSON
- `ensure_data_files()`: Initialize required data files

### tools/
Defines and executes tools that the agent can use to interact with the phone.
- `tools`: Array of tool definitions with schemas
- `execute_tool()`: Execute a tool by name with arguments
- Includes: battery status, WiFi info, GPS, clipboard, SMS/MMS, camera, file operations, task scheduling, and memory management

### llm/
Handles communication with the LLM via HTTP or MQTT.
- `request_llm_response()`: Send requests to LLM
- `normalize_llm_response()`: Normalize different response formats
- `process_llm_task()`: Main task processing loop with tool execution

### tasks/
Manages scheduled task execution (interval, daily, once).
- `schedule_task()`: Create a new scheduled task
- `list_tasks()`: List all scheduled tasks
- `cancel_task()`: Disable a scheduled task
- `run_scheduled_tasks()`: Execute tasks that are due

### memory/
Manages conversation history and user profile information.
- `append_history()`: Add message to conversation history
- `get_history_context()`: Retrieve recent conversation context
- `update_memory()`: Save notes to user profile

### sms/
Handles incoming SMS command detection and filtering.
- `check_for_sms_commands()`: Check for new SMS from user

### onboarding/
Provides interactive setup wizard for first-time configuration.
- `run_onboarding_flow()`: Interactive configuration process
- `check_termux_permissions()`: Verify required permissions

## Usage

### Initial Setup
First install Termux and Termux:API using the F-Droid app https://f-droid.org/
Open the Termux application and run the following commands:
```bash
termux-setup-storage
pkg update
pkg install python
pip install requests paho-mqtt
python3 android_agent.py --onboarding
```

### Running the Agent
```bash
python3 android_agent.py
```

## Adding New Features

### Adding a New Tool
1. Add tool definition to `tools/tool_definitions.py`
2. Add execution logic to `tools/tool_executor.py`

### Adding a New Module
1. Create directory under `termux-agent/`
2. Add `__init__.py` with exports
3. Create implementation files
4. Import in main `android_agent.py` as needed

## Dependencies
- Python 3.x
- paho-mqtt (for MQTT mode)
- requests (for HTTP mode)
- Termux (for Android integration)