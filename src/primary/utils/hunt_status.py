"""
Hunt Status Tracking Utility
This module provides functions to update hunt status in history entries across all *arr apps.
It tracks detailed status including download progress and protocol information.
"""

import logging
import time
import datetime
from src.primary.utils.history_utils import add_history_entry
from src.primary.settings_manager import get_advanced_setting

logger = logging.getLogger(__name__)

# Constants for hunt status values
STATUS_SEARCHING = "Searching"
STATUS_DOWNLOADING = "Downloading"  # Will include progress percentage when used
STATUS_DOWNLOADED = "Downloaded"
STATUS_FAILED = "Failed"

# Status tracking dictionary to track item processing timestamps
# Format: {app_type: {instance_name: {item_id: {'first_seen': timestamp, 'last_progress': progress}}}}
status_tracking = {}

def update_hunt_status(app_type, instance_name, item_id, item_data=None, queue_data=None, operation_type="missing"):
    """
    Update history with the current hunt status of an item including detailed queue information
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, lidarr, readarr, etc.)
    - instance_name: str - Name of the instance
    - item_id: str/int - ID of the item being processed
    - item_data: dict - Item data from the API (movie, series, album, etc.) - can be None if only queue data is available
    - queue_data: dict - Queue item data for this item, or None if not in queue
    - operation_type: str - Operation type for history entry (default: "missing")
    
    Returns:
    - str - The hunt status that was set
    - dict - Additional status information (progress, protocol, etc.)
    """
    item_id = str(item_id)  # Ensure item_id is a string for consistent comparison
    
    # Initialize or get status tracking entry for this item
    if app_type not in status_tracking:
        status_tracking[app_type] = {}
    if instance_name not in status_tracking[app_type]:
        status_tracking[app_type][instance_name] = {}
    
    now = time.time()
    
    # First check if there's an existing history entry to preserve the original timestamp
    from src.primary.history_manager import get_history
    existing_entries = get_history(app_type)
    existing_entry = None
    
    # Find the existing entry for this item_id if it exists
    for entry in existing_entries.get("entries", []):
        if str(entry.get("id", "")) == item_id and entry.get("instance_name") == instance_name:
            existing_entry = entry
            break
    try:
        # Get failure timeout setting
        declared_failure_minutes = get_advanced_setting("declared_item_failure_minutes", 15)
        
        # Common fields across all *arr apps
        item_name = ""
        has_file = False
        
        # Extra status information to track
        status_info = {
            "progress": None,
            "protocol": None,
            "status_detail": None
        }
        
        # Default hunt status if we can't determine it
        hunt_status = STATUS_SEARCHING
        
        # Get the name from item_data if available
        if item_data:
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
        
        # If we don't have a name yet but have an existing entry, use its name
        if not item_name and existing_entry:
            item_name = existing_entry.get('name', f"Item ID: {item_id}")
        
        # Determine hunt status based on file status and queue data
        if has_file:
            hunt_status = STATUS_DOWNLOADED
            # Item has been downloaded, remove from tracking
            if item_id in status_tracking[app_type].get(instance_name, {}):
                del status_tracking[app_type][instance_name][item_id]
        
        elif queue_data:
            # Item is in download queue, update details
            progress = queue_data.get('progress', 0)
            protocol = queue_data.get('protocol', 'unknown').capitalize()
            status_detail = queue_data.get('status', 'unknown').lower()
            
            # Determine if download is paused or active
            is_paused = status_detail == 'paused'
            
            # Set appropriate status with progress percentage
            if is_paused:
                hunt_status = f"Paused - {progress}%"
            else:
                hunt_status = f"{STATUS_DOWNLOADING} - {progress}%"
            
            # Add extra details
            status_info['progress'] = progress
            status_info['protocol'] = protocol
            status_info['status_detail'] = status_detail
            status_info['is_paused'] = is_paused
            
            # Update tracking info
            if item_id not in status_tracking[app_type].get(instance_name, {}):
                status_tracking[app_type][instance_name][item_id] = {'first_seen': now, 'last_progress': progress}
            else:
                status_tracking[app_type][instance_name][item_id]['last_progress'] = progress
        
        else:
            # Item is not in queue and doesn't have a file
            # Check if it's been tracked before
            tracked_info = status_tracking[app_type].get(instance_name, {}).get(item_id)
            
            if tracked_info:
                # Calculate minutes since first seen
                minutes_elapsed = (now - tracked_info['first_seen']) / 60
                
                # If it's been longer than the failure timeout, mark as failed
                if minutes_elapsed > declared_failure_minutes:
                    hunt_status = STATUS_FAILED
                    logger.info(f"[HUNTING] Marking {app_type} ID {item_id} as {STATUS_FAILED} after {minutes_elapsed:.1f} minutes")
                else:
                    hunt_status = STATUS_SEARCHING
            else:
                # First time seeing this item, add it to tracking
                status_tracking[app_type].setdefault(instance_name, {})[item_id] = {'first_seen': now, 'last_progress': 0}
                hunt_status = STATUS_SEARCHING
        
        # Create history entry with hunt status, preserving original timestamp if available
        history_entry = {
            "name": item_name,
            "instance_name": instance_name,
            "id": item_id,
            "operation_type": operation_type,
            "hunt_status": hunt_status,
            "protocol": status_info["protocol"]  # Include protocol information
        }
        
        # If we have an existing entry, use its timestamp and just update the status fields
        if existing_entry:
            # We're just updating the hunt status, not creating a new history entry
            # This ensures timestamps remain based on original request time
            from src.primary.history_manager import update_history_entry_status
            
            # Ensure we pass both the hunt status and protocol
            protocol = status_info["protocol"] if status_info["protocol"] else None
            
            # Call with original timestamp preservation
            update_result = update_history_entry_status(
                app_type, instance_name, item_id, hunt_status, protocol=protocol
            )
            
            if update_result:
                logger.info(f"[HUNTING] Updated existing history entry status for {app_type} ID {item_id}: {hunt_status} ({protocol or 'no protocol'})")
            else:
                # If update failed, create new entry as fallback
                add_history_entry(app_type, history_entry)
                logger.info(f"[HUNTING] Created new history entry after update failure for {app_type} ID {item_id}: {hunt_status}")
        else:
            # No existing entry found, create a new one
            add_history_entry(app_type, history_entry)
            logger.info(f"[HUNTING] Created new history entry with hunt status for {app_type} ID {item_id}: {hunt_status}")
        
        return hunt_status, status_info
        
    except Exception as e:
        logger.error(f"[HUNTING] Error updating hunt status for {app_type} ID {item_id}: {e}")
        return None, {}
        
def clear_stale_status_tracking():
    """
    Clear status tracking for items that haven't been updated recently
    This prevents memory leaks from items that are no longer being processed
    """
    now = time.time()
    declared_failure_minutes = get_advanced_setting("declared_item_failure_minutes", 15)
    timeout_seconds = declared_failure_minutes * 60 * 2  # Double the failure timeout
    
    cleared_count = 0
    
    for app_type in list(status_tracking.keys()):
        for instance_name in list(status_tracking[app_type].keys()):
            for item_id in list(status_tracking[app_type][instance_name].keys()):
                item_info = status_tracking[app_type][instance_name][item_id]
                
                # Remove items that haven't been updated in a while
                if now - item_info['first_seen'] > timeout_seconds:
                    del status_tracking[app_type][instance_name][item_id]
                    cleared_count += 1
    
    if cleared_count > 0:
        logger.debug(f"[HUNTING] Cleared {cleared_count} stale items from status tracking")
    
    return cleared_count
