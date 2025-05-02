import os
import json
import time
from datetime import datetime
import threading
import logging

# Create a logger
logger = logging.getLogger(__name__)

# Path will be /config/history in production
HISTORY_BASE_PATH = "/config/history"

# Lock to prevent race conditions during file operations
history_locks = {
    "sonarr": threading.Lock(),
    "radarr": threading.Lock(),
    "lidarr": threading.Lock(),
    "readarr": threading.Lock(),
    "whisparr": threading.Lock()
}

def ensure_history_dir():
    """Ensure the history directory exists"""
    try:
        os.makedirs(HISTORY_BASE_PATH, exist_ok=True)
        # Create app-specific files if they don't exist
        for app in history_locks.keys():
            history_file = os.path.join(HISTORY_BASE_PATH, f"{app}_history.json")
            if not os.path.exists(history_file):
                with open(history_file, 'w') as f:
                    json.dump([], f)
        return True
    except Exception as e:
        logger.error(f"Failed to create history directory: {str(e)}")
        return False

def add_history_entry(app_type, entry_data):
    """
    Add a new history entry
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - entry_data: dict with required fields:
        - name: str - Name of processed content
        - instance_name: str - Name of the instance
        - id: str - ID of the processed content
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return None
    
    if app_type not in history_locks:
        logger.error(f"Invalid app type: {app_type}")
        return None
    
    required_fields = ["name", "instance_name", "id"]
    for field in required_fields:
        if field not in entry_data:
            logger.error(f"Missing required field: {field}")
            return None
    
    # Create the entry with timestamp
    timestamp = int(time.time())
    entry = {
        "date_time": timestamp,
        "date_time_readable": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        "processed_info": entry_data["name"],
        "id": entry_data["id"],
        "instance_name": entry_data["instance_name"],
        "operation_type": entry_data.get("operation_type", "missing")  # Default to "missing" if not specified
    }
    
    history_file = os.path.join(HISTORY_BASE_PATH, f"{app_type}_history.json")
    
    # Thread-safe file operation
    with history_locks[app_type]:
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file doesn't exist or is corrupt, start with empty list
            history_data = []
        
        # Add new entry at the beginning for most recent first
        history_data.insert(0, entry)
        
        # Write back to file
        with open(history_file, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    logger.info(f"Added history entry for {app_type}: {entry_data['name']}")
    return entry

def get_history(app_type, search_query=None, page=1, page_size=20):
    """
    Get history entries for an app
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - search_query: str - Optional search query to filter results
    - page: int - Page number (1-based)
    - page_size: int - Number of entries per page
    
    Returns:
    - dict with entries, total_entries, and total_pages
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return {"entries": [], "total_entries": 0, "total_pages": 0, "current_page": 1}
    
    if app_type not in history_locks and app_type != "all":
        logger.error(f"Invalid app type: {app_type}")
        return {"entries": [], "total_entries": 0, "total_pages": 0, "current_page": 1}
    
    result = []
    
    if app_type == "all":
        # Combine histories from all apps
        all_history = []
        for app in history_locks.keys():
            history_file = os.path.join(HISTORY_BASE_PATH, f"{app}_history.json")
            try:
                with open(history_file, 'r') as f:
                    app_history = json.load(f)
                    all_history.extend(app_history)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Error reading history file for {app}: {str(e)}")
                continue
        
        # Sort by date_time in descending order
        result = sorted(all_history, key=lambda x: x["date_time"], reverse=True)
    else:
        # Get history for specific app
        history_file = os.path.join(HISTORY_BASE_PATH, f"{app_type}_history.json")
        try:
            with open(history_file, 'r') as f:
                result = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading history file for {app_type}: {str(e)}")
            result = []
    
    # Apply search filter if provided
    if search_query and search_query.strip():
        search_query = search_query.lower()
        result = [
            entry for entry in result if 
            search_query in entry.get("processed_info", "").lower() or
            search_query in entry.get("instance_name", "").lower() or
            search_query in str(entry.get("id", "")).lower()
        ]
    
    # Calculate pagination
    total_entries = len(result)
    total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1
    
    # Adjust page if out of bounds
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Get entries for the current page
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_entries = result[start_idx:end_idx]
    
    # Calculate "how long ago" for each entry
    current_time = int(time.time())
    for entry in paginated_entries:
        seconds_ago = current_time - entry["date_time"]
        entry["how_long_ago"] = format_time_ago(seconds_ago)
    
    return {
        "entries": paginated_entries,
        "total_entries": total_entries,
        "total_pages": total_pages,
        "current_page": page
    }

def format_time_ago(seconds):
    """Format seconds into a human-readable 'time ago' string"""
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    
    if days > 0:
        return f"{days} {'day' if days == 1 else 'days'} ago"
    elif hours > 0:
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    elif minutes > 0:
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    else:
        return f"{seconds} {'second' if seconds == 1 else 'seconds'} ago"

def clear_history(app_type):
    """
    Clear history for an app
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc) or 'all'
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return False
    
    if app_type == "all":
        # Clear all histories
        for app in history_locks.keys():
            history_file = os.path.join(HISTORY_BASE_PATH, f"{app}_history.json")
            with history_locks[app]:
                try:
                    with open(history_file, 'w') as f:
                        json.dump([], f)
                except Exception as e:
                    logger.error(f"Failed to clear history for {app}: {str(e)}")
                    return False
    elif app_type in history_locks:
        # Clear specific app history
        history_file = os.path.join(HISTORY_BASE_PATH, f"{app_type}_history.json")
        with history_locks[app_type]:
            try:
                with open(history_file, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"Failed to clear history for {app_type}: {str(e)}")
                return False
    else:
        logger.error(f"Invalid app type: {app_type}")
        return False
    
    logger.info(f"Cleared history for {app_type}")
    return True
