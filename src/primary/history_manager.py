import time
from datetime import datetime
import threading
import logging
from typing import Dict, Any, Optional

# Create a logger
logger = logging.getLogger(__name__)

# Import database
from src.primary.utils.database import get_database

# Lock to prevent race conditions during database operations
history_locks = {
    "sonarr": threading.Lock(),
    "radarr": threading.Lock(),
    "lidarr": threading.Lock(),
    "readarr": threading.Lock(),
    "whisparr": threading.Lock(),
    "eros": threading.Lock()
}

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
    
    # Thread-safe database operation
    with history_locks[app_type]:
        try:
            db = get_database()
            entry = db.add_history_entry(
                app_type=app_type,
                instance_name=instance_name,
                media_id=entry_data["id"],
                processed_info=entry_data["name"],
                operation_type=entry_data.get("operation_type", "missing"),
                discovered=False  # Default to false - will be updated by discovery tracker
            )
            
            # Add additional fields for compatibility
            entry["app_type"] = app_type  # Include app_type in the entry for display in UI
            
            logger.info(f"Added history entry for {app_type}-{instance_name}: {entry_data['name']}")
            
            # Send notification about this history entry
            try:
                # Import here to avoid circular imports
                from src.primary.notification_manager import send_history_notification
                send_history_notification(entry)
            except Exception as e:
                logger.error(f"Failed to send notification for history entry: {e}")
            
            return entry
            
        except Exception as e:
            logger.error(f"Database error adding history entry for {app_type}: {e}")
            return None

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
    if app_type not in history_locks and app_type != "all":
        logger.error(f"Invalid app type: {app_type}")
        return {"entries": [], "total_entries": 0, "total_pages": 0, "current_page": 1}
    
    try:
        db = get_database()
        result = db.get_history(
            app_type=app_type,
            search_query=search_query,
            page=page,
            page_size=page_size
        )
        
        logger.debug(f"Retrieved {len(result['entries'])} history entries for {app_type} (page {page})")
        return result
        
    except Exception as e:
        logger.error(f"Database error getting history for {app_type}: {e}")
        return {"entries": [], "total_entries": 0, "total_pages": 0, "current_page": 1}

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
    if app_type not in history_locks and app_type != "all":
        logger.error(f"Invalid app type: {app_type}")
        return False
    
    try:
        db = get_database()
        db.clear_history(app_type)
        logger.info(f"Successfully cleared history for {app_type}")
        return True
        
    except Exception as e:
        logger.error(f"Database error clearing history for {app_type}: {e}")
        return False

def handle_instance_rename(app_type, old_instance_name, new_instance_name):
    """
    Handle renaming of an instance by updating history entries in the database.
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - old_instance_name: str - Previous instance name
    - new_instance_name: str - New instance name
    
    Returns:
    - bool - Success or failure
    """
    if app_type not in history_locks:
        logger.error(f"Invalid app type: {app_type}")
        return False
    
    # If names are the same, nothing to do
    if old_instance_name == new_instance_name:
        return True
    
    logger.info(f"Handling instance rename for {app_type}: {old_instance_name} -> {new_instance_name}")
    
    # Thread-safe operation
    with history_locks[app_type]:
        try:
            db = get_database()
            db.handle_instance_rename(app_type, old_instance_name, new_instance_name)
            return True
            
        except Exception as e:
            logger.error(f"Database error renaming instance history: {e}")
            return False

def initialize_instance_history(app_type, instance_name):
    """
    Initialize or ensure history exists for a specific instance.
    This should be called whenever an instance is created or configured.
    
    Note: With database storage, no initialization is needed as entries are created on-demand.
    This function is kept for API compatibility.
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - instance_name: str - Name of the instance
    
    Returns:
    - str - Success message (for compatibility)
    """
    if app_type not in history_locks:
        logger.error(f"Invalid app type: {app_type}")
        return None
    
    logger.info(f"History initialized for {app_type}/{instance_name} (database-backed)")
    return f"Database history ready for {app_type}/{instance_name}"

def sync_history_files_with_instances():
    """
    Synchronize history with existing instances.
    
    Note: With database storage, no file synchronization is needed.
    This function is kept for API compatibility.
    
    Returns:
    - dict - Information about what was synchronized
    """
    result = {
        "success": True,
        "app_instances": {},
        "created_files": [],
        "error": None,
        "message": "Database-backed history requires no file synchronization"
    }
    
    try:
        # Get configured apps from database for reporting
        db = get_database()
        app_types = db.get_all_app_types()
        
        for app_type in app_types:
            if app_type in history_locks:
                result["app_instances"][app_type] = ["Database-backed"]
        
        logger.info("History synchronization complete (database-backed)")
        return result
        
    except Exception as e:
        logger.error(f"Error during history sync: {e}")
        result["error"] = str(e)
        result["success"] = False
        return result

# No longer need to run synchronization on module import since we're using database
logger.info("History manager initialized with database backend")
