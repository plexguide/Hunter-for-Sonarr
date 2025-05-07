"""
Hunt Status Tracking Utility
This module provides functions to update hunt status in history entries across all *arr apps.
"""

import logging
from src.primary.utils.history_utils import add_history_entry

logger = logging.getLogger(__name__)

def update_hunt_status(app_type, instance_name, item_id, item_data, queue_status=None, operation_type="missing"):
    """
    Update history with the current hunt status of an item
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, lidarr, readarr, etc.)
    - instance_name: str - Name of the instance
    - item_id: str/int - ID of the item being processed
    - item_data: dict - Item data from the API (movie, series, album, etc.)
    - queue_status: bool - Whether the item is in the download queue
    - operation_type: str - Operation type for history entry (default: "missing")
    
    Returns:
    - str - The hunt status that was set
    """
    
    # First check if there's an existing history entry to preserve the original timestamp
    from src.primary.history_manager import get_history
    existing_entries = get_history(app_type)
    existing_entry = None
    
    # Find the existing entry for this item_id if it exists
    for entry in existing_entries.get("entries", []):
        if str(entry.get("id", "")) == str(item_id) and entry.get("instance_name") == instance_name:
            existing_entry = entry
            break
    try:
        # Common fields across all *arr apps
        item_name = ""
        has_file = False
        
        # App-specific handling for title and file status
        if app_type == "radarr":
            item_name = item_data.get('title', f"Movie ID: {item_id}")
            has_file = item_data.get('hasFile', False)
        elif app_type == "sonarr":
            item_name = item_data.get('title', f"Series ID: {item_id}")
            has_file = item_data.get('hasFile', False)
        elif app_type == "lidarr":
            item_name = item_data.get('title', f"Artist ID: {item_id}")
            has_file = item_data.get('statistics', {}).get('trackFileCount', 0) > 0
        elif app_type == "readarr":
            item_name = item_data.get('title', f"Book ID: {item_id}")
            has_file = item_data.get('statistics', {}).get('bookFileCount', 0) > 0
        elif app_type == "whisparr" or app_type == "eros":
            item_name = item_data.get('title', f"Scene ID: {item_id}")
            has_file = item_data.get('hasFile', False)
        else:
            item_name = item_data.get('title', f"Item ID: {item_id}")
            # Try common options for file status
            has_file = (
                item_data.get('hasFile', False) or 
                item_data.get('statistics', {}).get('fileCount', 0) > 0
            )
        
        # Determine hunt status based on file status and queue status
        if has_file:
            hunt_status = "Downloaded"
        elif queue_status:
            hunt_status = "Found"
        else:
            hunt_status = "Searching"
        
        # Create history entry with hunt status, preserving original timestamp if available
        history_entry = {
            "name": item_name,
            "instance_name": instance_name,
            "id": item_id,
            "operation_type": operation_type,
            "hunt_status": hunt_status
        }
        
        # If we have an existing entry, use its timestamp and just update the hunt_status
        if existing_entry:
            # We're just updating the hunt status, not creating a new history entry
            # This ensures timestamps remain based on original request time
            from src.primary.history_manager import update_history_entry_status
            update_history_entry_status(app_type, instance_name, item_id, hunt_status)
            logger.info(f"[HUNTING] Updated existing history entry status for {app_type} ID {item_id}: {hunt_status}")
        else:
            # No existing entry found, create a new one
            add_history_entry(app_type, history_entry)
            logger.info(f"[HUNTING] Created new history entry with hunt status for {app_type} ID {item_id}: {hunt_status}")
        
        return hunt_status
        
    except Exception as e:
        logger.error(f"[HUNTING] Error updating hunt status for {app_type} ID {item_id}: {e}")
        return None
