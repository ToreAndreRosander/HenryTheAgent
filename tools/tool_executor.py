"""Tool execution logic."""
import os
import subprocess
import time


def call_termux(command):
    """Execute a termux command and return the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)


def execute_tool(name, args, config=None):
    """Execute a tool by name with given arguments."""
    
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
        num = args.get("number")
        if not num and config:
            num = config["user"]["phone_number"]
        msg = args.get("message", "")
        call_termux(f'termux-sms-send -n {num} "{msg}"')
        return f"SMS sendt til {num}"
    if name == "send_mms":
        num = args.get("number")
        if not num and config:
            num = config["user"]["phone_number"]
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
        # Import here to avoid circular dependencies
        from tasks.task_scheduler import schedule_task
        return schedule_task(args)
    if name == "list_tasks":
        from tasks.task_scheduler import list_tasks
        return list_tasks()
    if name == "cancel_task":
        from tasks.task_scheduler import cancel_task
        return cancel_task(args)
    if name == "update_memory":
        from memory.memory_manager import update_memory
        return update_memory(args, config)
    if name == "add_or_update_contact":
        from memory.memory_manager import add_or_update_contact
        return add_or_update_contact(args, config)
    if name == "update_short_term_memory":
        from memory.memory_manager import update_short_term_memory
        return update_short_term_memory(args, config)
    return "Ukjent verktøy"
