#!/usr/bin/env python3
"""
Cycle Tracker - Module for tracking application cycle times
"""

import os
import json
import datetime
import threading
from typing import Dict, Any, Optional

# Thread lock for updating cycle data
_lock = threading.Lock()

# Path to the cycle data file
_CYCLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'settings', 'cycle_data.json')

# Ensure directory exists
os.makedirs(os.path.dirname(_CYCLE_DATA_PATH), exist_ok=True)

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
    try:
        with open(_CYCLE_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving cycle data: {e}")

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
            "next_cycle": next_cycle_time.isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Save to disk
        _save_cycle_data(_cycle_data)

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
            return True
        return False
