#!/usr/bin/env python3
"""
Cycle Tracker - Module for tracking application cycle times
"""

import os
import json
import datetime
import time
import threading
from typing import Dict, Any, Optional
from src.primary.utils.config_paths import CONFIG_DIR, get_path

# Thread lock for updating cycle data
_lock = threading.Lock()

def _detect_environment():
    """Detect if we're running in Docker or bare metal environment"""
    return os.path.exists('/config') and os.path.exists('/app')

def _get_paths():
    """Get appropriate file paths using centralized config_paths"""
    # Use centralized path configuration for cross-platform compatibility
    cycle_data_path = get_path('settings', 'cycle_data.json')
    sleep_data_path = get_path('tally', 'sleep.json')
    
    # Web sleep data path - handle both Docker and bare metal
    if _detect_environment():
        # Docker environment
        web_sleep_data_path = os.path.join('/app', 'frontend', 'static', 'data', 'sleep.json')
    else:
        # Bare metal environment - use relative path from project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        web_sleep_data_path = os.path.join(base_dir, 'frontend', 'static', 'data', 'sleep.json')
    
    return cycle_data_path, sleep_data_path, web_sleep_data_path

# Get paths based on environment
_CYCLE_DATA_PATH, _SLEEP_DATA_PATH, _WEB_SLEEP_DATA_PATH = _get_paths()

print(f"[CycleTracker] Environment: {'Docker' if _detect_environment() else 'Bare Metal'}")
print(f"[CycleTracker] Config dir: {CONFIG_DIR}")
print(f"[CycleTracker] Sleep data path: {_SLEEP_DATA_PATH}")
print(f"[CycleTracker] Web sleep data path: {_WEB_SLEEP_DATA_PATH}")

# Ensure directories exist
os.makedirs(os.path.dirname(_CYCLE_DATA_PATH), exist_ok=True)
os.makedirs(os.path.dirname(_SLEEP_DATA_PATH), exist_ok=True)
os.makedirs(os.path.dirname(_WEB_SLEEP_DATA_PATH), exist_ok=True)

def ensure_all_apps_have_cyclelock():
    """
    Ensure all apps in sleep.json have the cyclelock field initialized.
    This fixes apps that were created before the cyclelock system was implemented.
    """
    try:
        if not os.path.exists(_SLEEP_DATA_PATH):
            print("[CycleTracker] No sleep.json found, nothing to initialize")
            return
        
        # Read current sleep data
        with open(_SLEEP_DATA_PATH, 'r') as f:
            sleep_data = json.load(f)
        
        updated = False
        for app_type, app_data in sleep_data.items():
            if 'cyclelock' not in app_data:
                # Default to True (running cycle) for Docker startup behavior
                app_data['cyclelock'] = True
                app_data['updated_at'] = datetime.datetime.utcnow().isoformat() + "Z"
                updated = True
                print(f"[CycleTracker] Initialized cyclelock=True for {app_type}")
        
        if updated:
            # Write back to both files
            with open(_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            print("[CycleTracker] Updated sleep.json with missing cyclelock fields")
        else:
            print("[CycleTracker] All apps already have cyclelock fields")
            
    except Exception as e:
        print(f"[CycleTracker] Error ensuring cyclelock fields: {e}")
        import traceback
        traceback.print_exc()

# Create empty sleep.json file if it doesn't exist
if not os.path.exists(_SLEEP_DATA_PATH):
    try:
        print(f"Creating initial sleep.json at {_SLEEP_DATA_PATH}")
        # Create initial empty structure
        initial_data = {}
        with open(_SLEEP_DATA_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
        print(f"Creating initial web sleep.json at {_WEB_SLEEP_DATA_PATH}")
        with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
    except Exception as e:
        print(f"Error creating initial sleep.json: {e}")
        import traceback
        traceback.print_exc()
else:
    # Check if existing file is valid JSON
    try:
        with open(_SLEEP_DATA_PATH, 'r') as f:
            test_data = json.load(f)
        print(f"[CycleTracker] Existing sleep.json is valid JSON with {len(test_data)} entries")
    except (json.JSONDecodeError, Exception) as e:
        print(f"[CycleTracker] Existing sleep.json is corrupted, recreating: {e}")
        try:
            # Backup corrupted file
            backup_path = f"{_SLEEP_DATA_PATH}.backup.{int(time.time())}"
            os.rename(_SLEEP_DATA_PATH, backup_path)
            print(f"[CycleTracker] Backed up corrupted file to {backup_path}")
            
            # Create new empty file
            with open(_SLEEP_DATA_PATH, 'w') as f:
                json.dump({}, f, indent=2)
            with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
                json.dump({}, f, indent=2)
            print(f"[CycleTracker] Created new sleep.json files")
        except Exception as recreate_e:
            print(f"[CycleTracker] Error recreating sleep.json: {recreate_e}")

# Ensure all existing apps have cyclelock fields
ensure_all_apps_have_cyclelock()

# In-memory cache of cycle times
_cycle_data: Dict[str, Any] = {}

def _load_cycle_data() -> Dict[str, Any]:
    """Load cycle data from disk"""
    if os.path.exists(_CYCLE_DATA_PATH):
        try:
            with open(_CYCLE_DATA_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cycle data: {e}")
    return {}

def _save_cycle_data(data: Dict[str, Any]) -> None:
    """Save cycle data to disk"""
    # First save to the original path for API access
    try:
        with open(_CYCLE_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved cycle data to {_CYCLE_DATA_PATH}")
    except Exception as e:
        print(f"Error saving cycle data to {_CYCLE_DATA_PATH}: {e}")
        import traceback
        traceback.print_exc()
    
    # Then save to the direct access path for frontend
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(_SLEEP_DATA_PATH), exist_ok=True)
        
        # Read existing sleep.json to preserve cyclelock fields
        existing_sleep_data = {}
        if os.path.exists(_SLEEP_DATA_PATH):
            try:
                with open(_SLEEP_DATA_PATH, 'r') as f:
                    existing_sleep_data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not read existing sleep.json: {e}")
                existing_sleep_data = {}
        
        # Convert to a simpler format for the frontend, preserving cyclelock
        frontend_data = {}
        for app, app_data in data.items():
            # Get existing cyclelock value or default to True
            existing_app_data = existing_sleep_data.get(app, {})
            cyclelock = existing_app_data.get('cyclelock', True)
            
            frontend_data[app] = {
                "next_cycle": app_data["next_cycle"],
                "remaining_seconds": _calculate_remaining_seconds(app_data["next_cycle"]),
                "updated_at": app_data["updated_at"],
                "cyclelock": cyclelock  # Preserve existing cyclelock value
            }
        
        # Debug output
        print(f"Writing sleep data to {_SLEEP_DATA_PATH}")
        print(f"Sleep data content: {frontend_data}")
        
        # Write the file
        with open(_SLEEP_DATA_PATH, 'w') as f:
            json.dump(frontend_data, f, indent=2)
        
        # Also write to web-accessible location
        with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
            json.dump(frontend_data, f, indent=2)
        
        # Verify file was created
        if os.path.exists(_SLEEP_DATA_PATH):
            print(f"Successfully saved sleep data to {_SLEEP_DATA_PATH}")
        else:
            print(f"WARNING: sleep.json file not found after write attempt")
    except Exception as e:
        print(f"Error saving sleep data to {_SLEEP_DATA_PATH}: {e}")
        import traceback
        traceback.print_exc()

def _get_user_timezone():
    """Get the user's selected timezone from general settings"""
    try:
        from src.primary import settings_manager
        general_settings = settings_manager.load_settings("general")
        timezone_name = general_settings.get("timezone", "UTC")
        
        # Import timezone handling
        import pytz
        try:
            user_tz = pytz.timezone(timezone_name)
            print(f"[CycleTracker] Using user timezone: {timezone_name}")
            return user_tz
        except pytz.UnknownTimeZoneError:
            print(f"[CycleTracker] Unknown timezone '{timezone_name}', falling back to UTC")
            return pytz.UTC
    except Exception as e:
        print(f"[CycleTracker] Error getting user timezone: {e}, using UTC")
        import pytz
        return pytz.UTC

def _calculate_remaining_seconds(next_cycle_iso: str) -> int:
    """Calculate remaining seconds until the next cycle"""
    try:
        # Get user's selected timezone
        user_tz = _get_user_timezone()
        
        # Clean up the ISO string to handle various malformed formats
        original_iso = next_cycle_iso
        
        # Remove any trailing 'Z' if there's already a timezone offset
        if '+' in next_cycle_iso and next_cycle_iso.endswith('Z'):
            next_cycle_iso = next_cycle_iso[:-1]
            print(f"[DEBUG] Removed trailing Z from ISO string with offset: {original_iso} -> {next_cycle_iso}")
        
        # Parse the ISO string more reliably
        if next_cycle_iso.endswith('Z'):
            # Remove the 'Z' and parse as UTC, then convert to user timezone
            next_cycle_str = next_cycle_iso[:-1]
            next_cycle = datetime.datetime.fromisoformat(next_cycle_str)
            # Make it timezone-aware UTC first, then convert to user timezone
            if next_cycle.tzinfo is None:
                import pytz
                next_cycle = pytz.UTC.localize(next_cycle)
            next_cycle = next_cycle.astimezone(user_tz)
        else:
            # Parse as-is and convert to user timezone
            next_cycle = datetime.datetime.fromisoformat(next_cycle_iso)
            if next_cycle.tzinfo is None:
                # If naive datetime, assume it's in user timezone
                next_cycle = user_tz.localize(next_cycle)
        
        # Get current time in user's timezone for consistent comparison
        now = datetime.datetime.now(user_tz)
        
        # Calculate the time difference in seconds
        delta = (next_cycle - now).total_seconds()
        
        # Return at least 0 (don't return negative values)
        result = max(0, int(delta))
        print(f"[DEBUG] Calculated remaining seconds for {original_iso}: {result} (now: {now.isoformat()}, next: {next_cycle.isoformat()})")
        return result
    except Exception as e:
        print(f"Error calculating remaining seconds for {next_cycle_iso}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def update_sleep_json(app_type: str, next_cycle_time: datetime.datetime, cyclelock: bool = None) -> None:
    """
    Update the sleep.json file directly for easier frontend access
    
    This function directly writes to sleep.json without using the _save_cycle_data function
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        next_cycle_time: When the next cycle will begin
        cyclelock: If provided, sets the cycle lock state (True = running, False = waiting)
    """
    # First check if we need to debug
    debug_mode = True  # Set to True to help troubleshoot file creation issues
    
    try:
        if debug_mode:
            print(f"[DEBUG] update_sleep_json called for {app_type}, cyclelock: {cyclelock}")
            print(f"[DEBUG] sleep.json path: {_SLEEP_DATA_PATH}")
        
        # Get the tally directory path
        tally_dir = os.path.dirname(_SLEEP_DATA_PATH)
        
        # Make sure the tally directory exists
        if not os.path.exists(tally_dir):
            if debug_mode:
                print(f"[DEBUG] Creating tally directory: {tally_dir}")
            os.makedirs(tally_dir, exist_ok=True)
            
            # Check if the directory was created successfully
            if os.path.exists(tally_dir):
                print(f"Successfully created directory: {tally_dir}")
            else:
                print(f"FAILED to create directory: {tally_dir}")
        
        # Get current data if the file exists
        sleep_data = {}
        if os.path.exists(_SLEEP_DATA_PATH):
            if debug_mode:
                print(f"[DEBUG] sleep.json exists, reading content")
            try:
                with open(_SLEEP_DATA_PATH, 'r') as f:
                    sleep_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: sleep.json exists but is not valid JSON, starting fresh")
                sleep_data = {}
            except Exception as e:
                print(f"Error reading sleep.json: {e}")
                sleep_data = {}
        else:
            if debug_mode:
                print(f"[DEBUG] sleep.json does not exist, creating new file")
        
        # Ensure next_cycle_time is timezone-aware and in user's selected timezone
        user_tz = _get_user_timezone()
        
        if next_cycle_time.tzinfo is None:
            # If naive datetime, assume it's in user's timezone
            next_cycle_time = user_tz.localize(next_cycle_time)
        elif next_cycle_time.tzinfo != user_tz:
            # Convert to user's timezone if it's in a different timezone
            next_cycle_time = next_cycle_time.astimezone(user_tz)
        
        # Remove microseconds for clean timestamps
        next_cycle_time = next_cycle_time.replace(microsecond=0)
        
        # Calculate remaining seconds based on user's timezone
        now_user_tz = datetime.datetime.now(user_tz).replace(microsecond=0)
        remaining_seconds = max(0, int((next_cycle_time - now_user_tz).total_seconds()))
        
        # Determine cyclelock value
        if cyclelock is None:
            # If not explicitly set, preserve existing value or default to True (cycle starting)
            existing_cyclelock = sleep_data.get(app_type, {}).get('cyclelock', True)
            cyclelock = existing_cyclelock
        
        # Update the app's data - store times in user's timezone format
        # Convert to naive datetime for clean JSON serialization
        next_cycle_naive = next_cycle_time.replace(tzinfo=None, microsecond=0)
        updated_at_naive = now_user_tz.replace(tzinfo=None, microsecond=0)
        
        # Generate ISO format with timezone info for clarity
        # Store timezone name for reference
        timezone_name = str(next_cycle_time.tzinfo)
        next_cycle_clean = next_cycle_time.isoformat()
        updated_at_clean = now_user_tz.isoformat()
        
        sleep_data[app_type] = {
            "next_cycle": next_cycle_clean,
            "remaining_seconds": remaining_seconds,
            "updated_at": updated_at_clean,
            "timezone": timezone_name,  # Store timezone info for frontend
            "cyclelock": cyclelock  # True = running cycle, False = waiting for cycle
        }
        
        # Write to the file
        if debug_mode:
            print(f"[DEBUG] Writing to sleep.json")
            print(f"[DEBUG] Data: {sleep_data}")
        
        try:
            # Write to the main sleep.json file
            with open(_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            
            # Also write to the web-accessible location
            with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            
            # Verify the files were created
            if os.path.exists(_SLEEP_DATA_PATH) and os.path.exists(_WEB_SLEEP_DATA_PATH):
                file_size = os.path.getsize(_SLEEP_DATA_PATH)
                web_file_size = os.path.getsize(_WEB_SLEEP_DATA_PATH)
                print(f"Successfully wrote sleep.json for {app_type} (size: {file_size} bytes)")
                print(f"Successfully wrote web sleep.json for {app_type} (size: {web_file_size} bytes)")
                print(f"  - Next cycle: {next_cycle_time.isoformat()}")
                print(f"  - Remaining seconds: {remaining_seconds}")
                print(f"  - Cycle lock: {cyclelock}")
            else:
                print(f"WARNING: sleep.json not found after write operation")
        except Exception as e:
            print(f"Error writing to sleep.json: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"Unhandled error in update_sleep_json for {app_type}: {e}")
        import traceback
        traceback.print_exc()

def update_next_cycle(app_type: str, next_cycle_time: datetime.datetime) -> None:
    """
    Update the next cycle time for an app
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        next_cycle_time: When the next cycle will begin
    """
    global _cycle_data
    
    with _lock:
        # Load fresh data in case another process updated it
        _cycle_data = _load_cycle_data()
        
        # Update the data
        _cycle_data[app_type] = {
            "next_cycle": next_cycle_time.isoformat() + "Z",  # Add Z to indicate UTC
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"  # Use UTC and add Z
        }
        
        # Save to disk (original method)
        _save_cycle_data(_cycle_data)
        
        # Also update sleep.json directly using the new function
        update_sleep_json(app_type, next_cycle_time)

def get_cycle_status(app_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the cycle status for all apps or a specific app
    
    Args:
        app_type: Optional app type to filter for
    
    Returns:
        Dict with cycle status information
    """
    global _cycle_data
    
    with _lock:
        # Load fresh data
        _cycle_data = _load_cycle_data()
        
        if app_type:
            # Return data for a specific app
            if app_type in _cycle_data:
                return {
                    "app": app_type,
                    "next_cycle": _cycle_data[app_type]["next_cycle"],
                    "updated_at": _cycle_data[app_type]["updated_at"]
                }
            else:
                return {
                    "app": app_type,
                    "error": f"No cycle data available for {app_type}"
                }
        else:
            # Return data for all apps
            result = {}
            for app, data in _cycle_data.items():
                result[app] = {
                    "next_cycle": data["next_cycle"],
                    "updated_at": data["updated_at"]
                }
            return result

def start_cycle(app_type: str) -> None:
    """
    Mark that a cycle has started for an app (set cyclelock to True)
    
    Args:
        app_type: The app that is starting a cycle
    """
    try:
        # Get current data if the file exists
        sleep_data = {}
        if os.path.exists(_SLEEP_DATA_PATH):
            try:
                with open(_SLEEP_DATA_PATH, 'r') as f:
                    sleep_data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error reading sleep.json for start_cycle: {e}")
                sleep_data = {}
        
        # Update cyclelock to True for this app
        if app_type in sleep_data:
            sleep_data[app_type]['cyclelock'] = True
            sleep_data[app_type]['updated_at'] = datetime.datetime.utcnow().isoformat() + "Z"
            
            # Write back to file
            with open(_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
                json.dump(sleep_data, f, indent=2)
            
            print(f"[CycleTracker] Started cycle for {app_type} (cyclelock = True)")
        else:
            print(f"[CycleTracker] Warning: No existing data for {app_type} to start cycle")
    except Exception as e:
        print(f"Error in start_cycle for {app_type}: {e}")
        import traceback
        traceback.print_exc()

def end_cycle(app_type: str, next_cycle_time: datetime.datetime) -> None:
    """
    Mark that a cycle has ended for an app (set cyclelock to False) and update next cycle time
    
    Args:
        app_type: The app that finished its cycle
        next_cycle_time: When the next cycle will begin
    """
    print(f"[CycleTracker] Ending cycle for {app_type}, next cycle at {next_cycle_time.isoformat()}")
    update_sleep_json(app_type, next_cycle_time, cyclelock=False)

def reset_cycle(app_type: str) -> bool:
    """
    Reset the cycle for a specific app (delete its cycle data and set cyclelock to True)
    
    Args:
        app_type: The app to reset
    
    Returns:
        True if successful, False otherwise
    """
    global _cycle_data
    
    with _lock:
        # Load fresh data
        _cycle_data = _load_cycle_data()
        
        # Remove the app's data if it exists
        if app_type in _cycle_data:
            del _cycle_data[app_type]
            _save_cycle_data(_cycle_data)
        
        # If sleep.json exists, update it to set cyclelock to True (cycle should start)
        try:
            if os.path.exists(_SLEEP_DATA_PATH):
                with open(_SLEEP_DATA_PATH, 'r') as f:
                    sleep_data = json.load(f)
                
                # Update the app's data to indicate cycle should start
                if app_type in sleep_data:
                    sleep_data[app_type]['cyclelock'] = True
                    sleep_data[app_type]['updated_at'] = datetime.datetime.utcnow().isoformat() + "Z"
                    print(f"[CycleTracker] Reset {app_type} - set cyclelock to True")
                else:
                    # Create new entry with cyclelock True
                    now = datetime.datetime.utcnow()
                    future_time = now + datetime.timedelta(minutes=15)  # Default 15 minutes
                    sleep_data[app_type] = {
                        "next_cycle": future_time.isoformat() + "Z",
                        "remaining_seconds": 900,  # 15 minutes
                        "updated_at": now.isoformat() + "Z",
                        "cyclelock": True
                    }
                    print(f"[CycleTracker] Reset {app_type} - created new entry with cyclelock True")
                
                # Write back
                with open(_SLEEP_DATA_PATH, 'w') as f:
                    json.dump(sleep_data, f, indent=2)
                with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
                    json.dump(sleep_data, f, indent=2)
        except Exception as e:
            print(f"Error updating sleep.json during reset: {e}")
            # Continue anyway - non-critical
        
        return True
