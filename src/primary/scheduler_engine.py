#!/usr/bin/env python3
"""
Scheduler Engine for Huntarr
Handles execution of scheduled actions from schedule.json
"""

import os
import json
import threading
import datetime
import time
import traceback
from typing import Dict, List, Any

from src.primary.utils.logger import get_logger

# Initialize logger
scheduler_logger = get_logger("scheduler")

# Scheduler constants
SCHEDULE_CHECK_INTERVAL = 60  # Check schedule every minute
SCHEDULE_DIR = "/config/scheduler"
SCHEDULE_FILE = os.path.join(SCHEDULE_DIR, "schedule.json")

# Track last executed actions to prevent duplicates
last_executed_actions = {}
stop_event = threading.Event()
scheduler_thread = None

def load_schedule():
    """Load the schedule configuration from file"""
    try:
        os.makedirs(SCHEDULE_DIR, exist_ok=True)  # Ensure directory exists
        
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r') as f:
                return json.load(f)
        else:
            scheduler_logger.warning(f"Schedule file not found: {SCHEDULE_FILE}")
            return {"global": [], "sonarr": [], "radarr": [], "lidarr": [], "readarr": [], "whisparr": [], "eros": []}
    except Exception as e:
        scheduler_logger.error(f"Error loading schedule: {e}")
        return {"global": [], "sonarr": [], "radarr": [], "lidarr": [], "readarr": [], "whisparr": [], "eros": []}

def execute_action(action_entry):
    """Execute a scheduled action"""
    action_type = action_entry.get("action")
    app_type = action_entry.get("app")
    app_id = action_entry.get("id")
    
    # Generate a unique key for this action to track execution
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    execution_key = f"{app_id}_{current_date}"
    
    # Check if this action was already executed today
    if execution_key in last_executed_actions:
        scheduler_logger.debug(f"Action {app_id} for {app_type} already executed today, skipping")
        return False  # Already executed
    
    try:
        if action_type == "pause":
            # Pause logic for global or specific app
            if app_type == "global":
                scheduler_logger.info("Executing global pause action")
                apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros']
                for app in apps:
                    config_file = f"/config/{app}.json"
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        config_data['enabled'] = False
                        with open(config_file, 'w') as f:
                            json.dump(config_data, f, indent=2)
                scheduler_logger.info("All apps paused successfully")
            else:
                scheduler_logger.info(f"Executing pause action for {app_type}")
                config_file = f"/config/{app_type}.json"
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    config_data['enabled'] = False
                    with open(config_file, 'w') as f:
                        json.dump(config_data, f, indent=2)
                scheduler_logger.info(f"{app_type} paused successfully")
        
        elif action_type == "resume":
            # Resume logic for global or specific app
            if app_type == "global":
                scheduler_logger.info("Executing global resume action")
                apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros']
                for app in apps:
                    config_file = f"/config/{app}.json"
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        config_data['enabled'] = True
                        with open(config_file, 'w') as f:
                            json.dump(config_data, f, indent=2)
                scheduler_logger.info("All apps resumed successfully")
            else:
                scheduler_logger.info(f"Executing resume action for {app_type}")
                config_file = f"/config/{app_type}.json"
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    config_data['enabled'] = True
                    with open(config_file, 'w') as f:
                        json.dump(config_data, f, indent=2)
                scheduler_logger.info(f"{app_type} resumed successfully")
        
        # Handle the API limit actions based on the predefined values
        elif action_type.startswith("API Limits "):
            # Extract the API limit value from the action type
            try:
                api_limit = int(action_type.replace("API Limits ", ""))
                
                if app_type == "global":
                    scheduler_logger.info(f"Setting global API cap to {api_limit}")
                    apps = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros']
                    for app in apps:
                        config_file = f"/config/{app}.json"
                        if os.path.exists(config_file):
                            with open(config_file, 'r') as f:
                                config_data = json.load(f)
                            config_data['hourly_cap'] = api_limit
                            with open(config_file, 'w') as f:
                                json.dump(config_data, f, indent=2)
                    scheduler_logger.info(f"API cap set to {api_limit} for all apps")
                else:
                    scheduler_logger.info(f"Setting API cap for {app_type} to {api_limit}")
                    config_file = f"/config/{app_type}.json"
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        config_data['hourly_cap'] = api_limit
                        with open(config_file, 'w') as f:
                            json.dump(config_data, f, indent=2)
                    scheduler_logger.info(f"API cap set to {api_limit} for {app_type}")
            except ValueError:
                scheduler_logger.error(f"Invalid API limit format: {action_type}")
                return False
        
        # Mark this action as executed for today
        last_executed_actions[execution_key] = datetime.datetime.now()
        return True
    
    except Exception as e:
        scheduler_logger.error(f"Error executing action {action_type} for {app_type}: {e}")
        scheduler_logger.error(traceback.format_exc())
        return False

def should_execute_schedule(schedule_entry):
    """Check if a schedule entry should be executed now"""
    if not schedule_entry.get("enabled", True):
        return False
    
    # Check if specific days are configured
    days = schedule_entry.get("days", [])
    if days:
        # If days array is not empty, check if today is in the list
        current_day = datetime.datetime.now().strftime("%A").lower()  # e.g., 'monday'
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }
        
        today_index = day_map.get(current_day)
        if today_index is None or today_index not in days:
            return False
    
    current_time = datetime.datetime.now()
    schedule_hour = schedule_entry.get("time", {}).get("hour")
    schedule_minute = schedule_entry.get("time", {}).get("minute")
    
    if schedule_hour is None or schedule_minute is None:
        scheduler_logger.warning(f"Schedule entry missing time information: {schedule_entry}")
        return False
    
    # Check if the current time matches the scheduled time
    # Use a 5-minute window to ensure we don't miss it
    if current_time.hour == schedule_hour:
        # Execute if we're within 5 minutes after the scheduled time
        # This handles cases where the scheduler isn't running exactly at the specified time
        return current_time.minute >= schedule_minute and current_time.minute < schedule_minute + 5
    
    return False

def check_and_execute_schedules():
    """Check all schedules and execute those that should run now"""
    try:
        scheduler_logger.debug("Checking schedules")
        schedule_data = load_schedule()
        
        # Process all app-specific and global schedules
        for app_type, schedules in schedule_data.items():
            for schedule in schedules:
                if should_execute_schedule(schedule):
                    scheduler_logger.info(f"Executing schedule for {app_type}: {schedule}")
                    execute_action(schedule)
    
    except Exception as e:
        scheduler_logger.error(f"Error checking and executing schedules: {e}")
        scheduler_logger.error(traceback.format_exc())

def scheduler_loop():
    """Main scheduler loop - runs in a background thread"""
    scheduler_logger.info("Scheduler engine started")
    
    # Clean up expired entries from last_executed_actions
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    for key in list(last_executed_actions.keys()):
        if last_executed_actions[key] < yesterday:
            del last_executed_actions[key]
    
    while not stop_event.is_set():
        try:
            check_and_execute_schedules()
            
            # Sleep until the next check
            stop_event.wait(SCHEDULE_CHECK_INTERVAL)
            
        except Exception as e:
            scheduler_logger.error(f"Error in scheduler loop: {e}")
            scheduler_logger.error(traceback.format_exc())
            # Sleep briefly to avoid rapidly repeating errors
            time.sleep(5)
    
    scheduler_logger.info("Scheduler engine stopped")

def start_scheduler():
    """Start the scheduler engine"""
    global scheduler_thread
    
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_logger.info("Scheduler already running")
        return
    
    # Reset the stop event
    stop_event.clear()
    
    # Create and start the scheduler thread
    scheduler_thread = threading.Thread(target=scheduler_loop, name="SchedulerEngine", daemon=True)
    scheduler_thread.start()
    
    scheduler_logger.info(f"Scheduler engine started. Thread is alive: {scheduler_thread.is_alive()}")
    return True

def stop_scheduler():
    """Stop the scheduler engine"""
    global scheduler_thread
    
    if not scheduler_thread or not scheduler_thread.is_alive():
        scheduler_logger.info("Scheduler not running")
        return
    
    # Signal the thread to stop
    stop_event.set()
    
    # Wait for the thread to terminate (with timeout)
    scheduler_thread.join(timeout=5.0)
    
    if scheduler_thread.is_alive():
        scheduler_logger.warning("Scheduler did not terminate gracefully")
    else:
        scheduler_logger.info("Scheduler stopped gracefully")
