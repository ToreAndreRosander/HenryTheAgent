"""Task scheduling and execution logic."""
import json
import time
from datetime import datetime, timedelta
from storage import TASKS_FILE, load_json, save_json


def schedule_task(args):
    """Schedule a new task."""
    tasks = load_json(TASKS_FILE, [])
    task_id = f"task_{int(time.time())}"
    schedule_type = args.get("schedule_type", "interval")
    now = datetime.utcnow()
    task = {
        "id": task_id,
        "name": args.get("name", task_id),
        "schedule_type": schedule_type,
        "interval_minutes": args.get("interval_minutes"),
        "daily_time": args.get("daily_time"),
        "run_at": args.get("run_at"),
        "actions": args.get("actions", []),
        "last_run": None,
        "next_run": None,
        "enabled": True
    }

    if schedule_type == "interval":
        interval_minutes = int(args.get("interval_minutes", 0))
        if interval_minutes <= 0:
            return "Ugyldig intervall"
        task["interval_minutes"] = interval_minutes
        task["next_run"] = (now + timedelta(minutes=interval_minutes)).isoformat()
    elif schedule_type == "daily":
        daily_time = args.get("daily_time")
        if not daily_time or len(daily_time.split(":")) != 2:
            return "Ugyldig tidspunkt for daily (HH:MM)"
        hour, minute = daily_time.split(":")
        next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        task["daily_time"] = daily_time
        task["next_run"] = next_run.isoformat()
    elif schedule_type == "once":
        run_at = args.get("run_at")
        if not run_at:
            return "Ugyldig tidspunkt for once (ISO8601)"
        try:
            next_run = datetime.fromisoformat(run_at)
        except ValueError:
            return "Ugyldig tidspunkt for once (ISO8601)"
        task["run_at"] = run_at
        task["next_run"] = next_run.isoformat()
    else:
        return "Ugyldig schedule_type"

    tasks.append(task)
    save_json(TASKS_FILE, tasks)
    return f"Oppgave planlagt: {task_id}"


def list_tasks():
    """List all scheduled tasks."""
    tasks = load_json(TASKS_FILE, [])
    return json.dumps(tasks, ensure_ascii=False, indent=2)


def cancel_task(args):
    """Cancel a scheduled task."""
    task_id = args.get("task_id")
    tasks = load_json(TASKS_FILE, [])
    updated = False
    for task in tasks:
        if task.get("id") == task_id:
            task["enabled"] = False
            updated = True
    save_json(TASKS_FILE, tasks)
    return "Oppgave deaktivert" if updated else "Fant ikke oppgave"


def run_scheduled_tasks():
    """Execute scheduled tasks that are due."""
    from tools.tool_executor import execute_tool
    
    tasks = load_json(TASKS_FILE, [])
    now = datetime.utcnow()
    changed = False

    for task in tasks:
        if not task.get("enabled", True):
            continue
        next_run = task.get("next_run")
        if not next_run:
            continue
        if datetime.fromisoformat(next_run) > now:
            continue

        last_result = ""
        for action in task.get("actions", []):
            tool_name = action.get("tool_name")
            tool_args = action.get("tool_args", {})
            resolved_args = {}
            for key, value in tool_args.items():
                if isinstance(value, str):
                    resolved_args[key] = value.replace("{last_result}", last_result)
                else:
                    resolved_args[key] = value
            last_result = execute_tool(tool_name, resolved_args)

        task["last_run"] = now.isoformat()
        schedule_type = task.get("schedule_type", "interval")
        if schedule_type == "interval":
            interval_minutes = int(task.get("interval_minutes", 0))
            task["next_run"] = (now + timedelta(minutes=interval_minutes)).isoformat()
        elif schedule_type == "daily":
            daily_time = task.get("daily_time", "06:00")
            hour, minute = daily_time.split(":")
            next_run_dt = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if next_run_dt <= now:
                next_run_dt += timedelta(days=1)
            task["next_run"] = next_run_dt.isoformat()
        elif schedule_type == "once":
            task["enabled"] = False
        else:
            task["enabled"] = False
        changed = True

    if changed:
        save_json(TASKS_FILE, tasks)
