#!/usr/bin/env python3
"""
Cycle Tracker - Module for tracking application cycle times
"""

import os
import json
import datetime
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

# Create empty sleep.json file if it doesn't exist
if not os.path.exists(_SLEEP_DATA_PATH):
    try:
        print(f"Creating initial sleep.json at {_SLEEP_DATA_PATH}")
        with open(_SLEEP_DATA_PATH, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"Creating initial web sleep.json at {_WEB_SLEEP_DATA_PATH}")
        with open(_WEB_SLEEP_DATA_PATH, 'w') as f:
            json.dump({}, f, indent=2)
    except Exception as e:
        print(f"Error creating initial sleep.json: {e}")
        import traceback
        traceback.print_exc()

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
        
        # Convert to a simpler format for the frontend
        frontend_data = {}
        for app, app_data in data.items():
            frontend_data[app] = {
                "next_cycle": app_data["next_cycle"],
                "remaining_seconds": _calculate_remaining_seconds(app_data["next_cycle"]),
                "updated_at": app_data["updated_at"]
            }
        
        # Debug output
        print(f"Writing sleep data to {_SLEEP_DATA_PATH}")
        print(f"Sleep data content: {frontend_data}")
        
        # Write the file
        with open(_SLEEP_DATA_PATH, 'w') as f:
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

def _calculate_remaining_seconds(next_cycle_iso: str) -> int:
    """Calculate remaining seconds until the next cycle"""
    try:
        next_cycle = datetime.datetime.fromisoformat(next_cycle_iso)
        # Use UTC time for consistency
        now = datetime.datetime.utcnow()
        
        # If next_cycle doesn't have timezone info, assume it's UTC
        if next_cycle.tzinfo is None:
            # Convert to UTC if no timezone info
            pass
        else:
            # Convert to UTC if it has timezone info
            next_cycle = next_cycle.utctimetuple()
            next_cycle = datetime.datetime(*next_cycle[:6])
        
        # Calculate the time difference in seconds
        delta = (next_cycle - now).total_seconds()
        
        # Return at least 0 (don't return negative values)
        return max(0, int(delta))
    except Exception as e:
        print(f"Error calculating remaining seconds: {e}")
        return 0

def update_sleep_json(app_type: str, next_cycle_time: datetime.datetime) -> None:
    """
    Update the sleep.json file directly for easier frontend access
    
    This function directly writes to sleep.json without using the _save_cycle_data function
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        next_cycle_time: When the next cycle will begin
    """
    # First check if we need to debug
    debug_mode = True  # Set to True to help troubleshoot file creation issues
    
    try:
        if debug_mode:
            print(f"[DEBUG] update_sleep_json called for {app_type}")
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
        
        # Calculate remaining seconds
        now = datetime.datetime.utcnow()  # Use UTC for consistency
        remaining_seconds = max(0, int((next_cycle_time - now).total_seconds()))
        
        # Update the app's data - store times in UTC format
        sleep_data[app_type] = {
            "next_cycle": next_cycle_time.isoformat() + "Z",  # Add Z to indicate UTC
            "remaining_seconds": remaining_seconds,
            "updated_at": now.isoformat() + "Z"  # Add Z to indicate UTC
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

def reset_cycle(app_type: str) -> bool:
    """
    Reset the cycle for a specific app (delete its cycle data)
    
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
            
            # If sleep.json exists, update it as well
            try:
                if os.path.exists(_SLEEP_DATA_PATH):
                    with open(_SLEEP_DATA_PATH, 'r') as f:
                        sleep_data = json.load(f)
                    
                    # Remove the app's data
                    if app_type in sleep_data:
                        del sleep_data[app_type]
                    
                    # Write back
                    with open(_SLEEP_DATA_PATH, 'w') as f:
                        json.dump(sleep_data, f, indent=2)
            except Exception as e:
                print(f"Error updating sleep.json during reset: {e}")
                # Continue anyway - non-critical
            
            return True
        return False
