import os
import json
import time
from datetime import datetime
import threading
import logging
import pathlib

# Create a logger
logger = logging.getLogger(__name__)

# Path will be /config/history in production
HISTORY_BASE_PATH = pathlib.Path("/config/history")

# Lock to prevent race conditions during file operations
history_locks = {
    "sonarr": threading.Lock(),
    "radarr": threading.Lock(),
    "lidarr": threading.Lock(),
    "readarr": threading.Lock(),
    "whisparr": threading.Lock(),
    "eros": threading.Lock(),
    "swaparr": threading.Lock()
}

def ensure_history_dir():
    """Ensure the history directory exists with app-specific subdirectories"""
    try:
        # Create base directory
        HISTORY_BASE_PATH.mkdir(exist_ok=True, parents=True)
        
        # Create app-specific directories
        for app in history_locks.keys():
            app_dir = HISTORY_BASE_PATH / app
            app_dir.mkdir(exist_ok=True, parents=True)
                    
        return True
    except Exception as e:
        logger.error(f"Failed to create history directory: {str(e)}")
        return False

def get_history_file_path(app_type, instance_name=None):
    """Get the appropriate history file path based on app type and instance name"""
    # If no instance name is provided, use "Default"
    if instance_name is None:
        instance_name = "Default"
    
    # Create safe filename from instance name (same as in stateful_manager.py)
    safe_instance_name = "".join([c if c.isalnum() else "_" for c in instance_name])
    return HISTORY_BASE_PATH / app_type / f"{safe_instance_name}.json"

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
    
    # Log the instance name for debugging
    instance_name = entry_data["instance_name"]
    logger.debug(f"Adding history entry for {app_type} with instance_name: '{instance_name}'")
    
    # Create the entry with timestamp
    timestamp = int(time.time())
    entry = {
        "date_time": timestamp,
        "date_time_readable": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        "processed_info": entry_data["name"],
        "id": entry_data["id"],
        "instance_name": instance_name,  # Use the instance_name we extracted above
        "operation_type": entry_data.get("operation_type", "missing"),  # Default to "missing" if not specified
        "app_type": app_type,  # Include app_type in the entry for display in UI
        "hunt_status": entry_data.get("hunt_status", "Not Tracked")  # Add hunt status field
    }
    
    history_file = get_history_file_path(app_type, instance_name)
    logger.debug(f"Writing to history file: {history_file}")
    
    # Make sure the parent directory exists
    history_file.parent.mkdir(exist_ok=True, parents=True)
    
    # Thread-safe file operation
    with history_locks[app_type]:
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
            else:
                history_data = []
        except (json.JSONDecodeError, FileNotFoundError):
            # If file doesn't exist or is corrupt, start with empty list
            history_data = []
        
        # Add new entry at the beginning for most recent first
        history_data.insert(0, entry)
        
        # Write back to file
        with open(history_file, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    logger.info(f"Added history entry for {app_type}-{instance_name}: {entry_data['name']}")
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
        # Combine histories from all apps and their instances
        for app in history_locks.keys():
            app_dir = HISTORY_BASE_PATH / app
            
            # Find and read all instance files
            if app_dir.exists():
                for history_file in app_dir.glob("*.json"):
                    try:
                        with open(history_file, 'r') as f:
                            instance_history = json.load(f)
                            result.extend(instance_history)
                            logger.debug(f"Read {len(instance_history)} entries from {history_file}")
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        logger.warning(f"Error reading instance history file {history_file}: {str(e)}")
    else:
        # Get history for specific app - combine all instances
        app_dir = HISTORY_BASE_PATH / app_type
        
        # Make sure app directory exists
        app_dir.mkdir(exist_ok=True, parents=True)
        
        # Read from all instance files
        if app_dir.exists():
            instance_files = list(app_dir.glob("*.json"))
            logger.debug(f"Found {len(instance_files)} instance files for {app_type}: {[f.name for f in instance_files]}")
            
            for history_file in instance_files:
                try:
                    with open(history_file, 'r') as f:
                        instance_history = json.load(f)
                        result.extend(instance_history)
                        logger.debug(f"Read {len(instance_history)} entries from {history_file}")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading instance history file {history_file}: {e}")
    
    # Sort by date_time in descending order
    result = sorted(result, key=lambda x: x["date_time"], reverse=True)
    
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
    - app_type: str - The app type (sonarr, radarr, etc) or "all" to clear all history
    
    Returns:
    - bool - Success or failure
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return False
    
    if app_type not in history_locks and app_type != "all":
        logger.error(f"Invalid app type: {app_type}")
        return False
    
    try:
        if app_type == "all":
            # Clear all history files for all apps
            for app in history_locks.keys():
                # Clear all instance files
                app_dir = HISTORY_BASE_PATH / app
                # Ensure directory exists
                app_dir.mkdir(exist_ok=True, parents=True)
                
                if app_dir.exists():
                    instance_files = list(app_dir.glob("*.json"))
                    logger.debug(f"Found {len(instance_files)} instance files to clear for {app}")
                    
                    for history_file in instance_files:
                        with open(history_file, 'w') as f:
                            json.dump([], f)
                            logger.debug(f"Cleared instance history file: {history_file}")
        else:
            # Clear all instance files for specific app
            app_dir = HISTORY_BASE_PATH / app_type
            # Ensure directory exists
            app_dir.mkdir(exist_ok=True, parents=True)
            
            if app_dir.exists():
                instance_files = list(app_dir.glob("*.json"))
                logger.debug(f"Found {len(instance_files)} instance files to clear for {app_type}")
                
                for history_file in instance_files:
                    with open(history_file, 'w') as f:
                        json.dump([], f)
                        logger.debug(f"Cleared instance history file: {history_file}")
        
        logger.info(f"Successfully cleared history for {app_type}")
        return True
    except Exception as e:
        logger.error(f"Error clearing history for {app_type}: {str(e)}")
        return False

def handle_instance_rename(app_type, old_instance_name, new_instance_name):
    """
    Handle renaming of an instance by moving history entries to a new file.
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - old_instance_name: str - Previous instance name
    - new_instance_name: str - New instance name
    
    Returns:
    - bool - Success or failure
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return False
    
    if app_type not in history_locks:
        logger.error(f"Invalid app type: {app_type}")
        return False
    
    # If names are the same, nothing to do
    if old_instance_name == new_instance_name:
        return True
    
    logger.info(f"Handling instance rename for {app_type}: {old_instance_name} -> {new_instance_name}")
    
    # Get paths for old and new history files
    old_file = get_history_file_path(app_type, old_instance_name)
    new_file = get_history_file_path(app_type, new_instance_name)
    
    # Ensure parent directories exist
    new_file.parent.mkdir(exist_ok=True, parents=True)
    
    # Thread-safe operation
    with history_locks[app_type]:
        try:
            # Load old data if it exists
            old_data = []
            if old_file.exists():
                try:
                    with open(old_file, 'r') as f:
                        old_data = json.load(f)
                    logger.info(f"Loaded {len(old_data)} history entries from {old_file}")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading old history file {old_file}: {e}")
            
            # Update instance_name in all entries
            for entry in old_data:
                entry["instance_name"] = new_instance_name
            
            # Create or load new file
            new_data = []
            if new_file.exists():
                try:
                    with open(new_file, 'r') as f:
                        new_data = json.load(f)
                    logger.info(f"Loaded {len(new_data)} existing history entries from {new_file}")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading new history file {new_file}: {e}")
            
            # Merge data, avoiding duplicates
            existing_keys = {(entry.get("id", ""), entry.get("date_time", 0)) for entry in new_data}
            for entry in old_data:
                entry_key = (entry.get("id", ""), entry.get("date_time", 0))
                if entry_key not in existing_keys:
                    new_data.append(entry)
            
            # Sort by timestamp
            new_data = sorted(new_data, key=lambda x: x.get("date_time", 0), reverse=True)
            
            # Save merged data to new file
            with open(new_file, 'w') as f:
                json.dump(new_data, f, indent=2)
            logger.info(f"Saved {len(new_data)} history entries to {new_file}")
            
            # Optionally delete old file if it exists
            if old_file.exists():
                old_file.unlink()
                logger.info(f"Deleted old history file {old_file}")
            
            return True
        except Exception as e:
            logger.error(f"Error renaming instance history: {e}")
            return False

def initialize_instance_history(app_type, instance_name):
    """
    Initialize or ensure history file exists for a specific instance.
    This should be called whenever an instance is created or configured.
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - instance_name: str - Name of the instance
    
    Returns:
    - str - Path to the history file
    """
    if not ensure_history_dir():
        logger.error("Could not ensure history directory exists")
        return None
    
    if app_type not in history_locks:
        logger.error(f"Invalid app type: {app_type}")
        return None
    
    try:
        # Get the history file path
        history_file = get_history_file_path(app_type, instance_name)
        
        # Ensure parent directory exists
        history_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Create the file if it doesn't exist
        if not history_file.exists():
            with open(history_file, 'w') as f:
                json.dump([], f)
            logger.info(f"Created history file for {app_type}/{instance_name}: {history_file}")
        
        return str(history_file)
    except Exception as e:
        logger.error(f"Error initializing history for {app_type}/{instance_name}: {e}")
        return None

def sync_history_files_with_instances():
    """
    Synchronize history files with existing instances.
    This ensures that every instance has a corresponding history file.
    
    Returns:
    - dict - Information about what was synchronized
    """
    result = {
        "success": False,
        "app_instances": {},
        "created_files": [],
        "error": None
    }
    
    try:
        # First ensure history directories exist
        ensure_history_dir()
        
        # Load settings for each app type to find instances
        for app_type in history_locks.keys():
            app_dir = HISTORY_BASE_PATH / app_type
            app_dir.mkdir(exist_ok=True, parents=True)
            
            result["app_instances"][app_type] = []
            
            # Let's check for instance settings from settings directory
            instances_dir = pathlib.Path("/config") / app_type
            if instances_dir.exists():
                for instance_file in instances_dir.glob("*.json"):
                    try:
                        # Extract instance name from filename
                        instance_name = instance_file.stem
                        result["app_instances"][app_type].append(instance_name)
                        logger.info(f"Found instance for {app_type}: {instance_name}")
                        
                        # Create history file for this instance if it doesn't exist
                        history_file = get_history_file_path(app_type, instance_name)
                        if not history_file.exists():
                            history_file.parent.mkdir(exist_ok=True, parents=True)
                            with open(history_file, 'w') as f:
                                json.dump([], f)
                            logger.info(f"Created history file for {app_type}/{instance_name}: {history_file}")
                            result["created_files"].append(str(history_file))
                    except Exception as e:
                        logger.error(f"Error processing instance file {instance_file}: {e}")
        
        result["success"] = True
        return result
    except Exception as e:
        logger.error(f"Error syncing history files with instances: {e}")
        result["error"] = str(e)
        return result

# Run the synchronization on module import
sync_result = sync_history_files_with_instances()
logger.info(f"History synchronization result: {sync_result}")
