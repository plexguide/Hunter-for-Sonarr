"""
Implementation of the swaparr functionality to detect and remove stalled downloads in Starr apps.
Based on the functionality provided by https://github.com/ThijmenGThN/swaparr
"""

import os
import json
import time
from datetime import datetime
import requests

from src.primary.utils.logger import get_logger
from src.primary.settings_manager import load_settings
from src.primary.state import get_state_file_path

# Create logger
swaparr_logger = get_logger("swaparr")

# Create state directory for tracking strikes
SWAPARR_STATE_DIR = os.path.join(os.getenv("CONFIG_DIR", "/config"), "swaparr")

def ensure_state_directory(app_name):
    """Ensure the state directory exists for tracking strikes for a specific app"""
    app_state_dir = os.path.join(SWAPARR_STATE_DIR, app_name)
    if not os.path.exists(app_state_dir):
        os.makedirs(app_state_dir, exist_ok=True)
        swaparr_logger.info(f"Created swaparr state directory for {app_name}: {app_state_dir}")
    return app_state_dir

def load_strike_data(app_name):
    """Load strike data for a specific app"""
    app_state_dir = ensure_state_directory(app_name)
    strike_file = os.path.join(app_state_dir, "strikes.json")
    
    if not os.path.exists(strike_file):
        return {}
    
    try:
        with open(strike_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        swaparr_logger.error(f"Error loading strike data for {app_name}: {str(e)}")
        return {}

def save_strike_data(app_name, strike_data):
    """Save strike data for a specific app"""
    app_state_dir = ensure_state_directory(app_name)
    strike_file = os.path.join(app_state_dir, "strikes.json")
    
    try:
        with open(strike_file, 'w') as f:
            json.dump(strike_data, f, indent=2)
    except IOError as e:
        swaparr_logger.error(f"Error saving strike data for {app_name}: {str(e)}")

def parse_time_string_to_seconds(time_string):
    """Parse a time string like '2h', '30m', '1d' to seconds"""
    if not time_string:
        return 7200  # Default 2 hours
    
    unit = time_string[-1].lower()
    try:
        value = int(time_string[:-1])
    except ValueError:
        swaparr_logger.error(f"Invalid time string: {time_string}, using default 2 hours")
        return 7200
    
    if unit == 'd':
        return value * 86400  # Days to seconds
    elif unit == 'h':
        return value * 3600   # Hours to seconds
    elif unit == 'm':
        return value * 60     # Minutes to seconds
    else:
        swaparr_logger.error(f"Unknown time unit in: {time_string}, using default 2 hours")
        return 7200

def parse_size_string_to_bytes(size_string):
    """Parse a size string like '25GB', '1TB' to bytes"""
    if not size_string:
        return 25 * 1024 * 1024 * 1024  # Default 25GB
    
    # Extract the numeric part and unit
    unit = ""
    for i in range(len(size_string) - 1, -1, -1):
        if not size_string[i].isalpha():
            value = float(size_string[:i+1])
            unit = size_string[i+1:].upper()
            break
    else:
        swaparr_logger.error(f"Invalid size string: {size_string}, using default 25GB")
        return 25 * 1024 * 1024 * 1024
    
    # Convert to bytes based on unit
    if unit == 'B':
        return int(value)
    elif unit == 'KB':
        return int(value * 1024)
    elif unit == 'MB':
        return int(value * 1024 * 1024)
    elif unit == 'GB':
        return int(value * 1024 * 1024 * 1024)
    elif unit == 'TB':
        return int(value * 1024 * 1024 * 1024 * 1024)
    else:
        swaparr_logger.error(f"Unknown size unit in: {size_string}, using default 25GB")
        return 25 * 1024 * 1024 * 1024

def get_queue_items(app_name, api_url, api_key, api_timeout=120):
    """Get download queue items from a Starr app API"""
    api_version_map = {
        "radarr": "v3",
        "sonarr": "v3",
        "lidarr": "v1",
        "readarr": "v1",
        "whisparr": "v3"
    }
    
    api_version = api_version_map.get(app_name, "v3")
    queue_url = f"{api_url.rstrip('/')}/api/{api_version}/queue"
    headers = {'X-Api-Key': api_key}
    
    try:
        response = requests.get(queue_url, headers=headers, timeout=api_timeout)
        response.raise_for_status()
        queue_data = response.json()
        
        # Normalize the response based on app type
        if app_name in ["radarr", "whisparr"]:
            return parse_queue_items(queue_data["records"], "movie", app_name)
        elif app_name == "sonarr":
            return parse_queue_items(queue_data["records"], "series", app_name)
        elif app_name == "lidarr":
            return parse_queue_items(queue_data["records"], "album", app_name)
        elif app_name == "readarr":
            return parse_queue_items(queue_data["records"], "book", app_name)
        else:
            swaparr_logger.error(f"Unknown app type: {app_name}")
            return []
            
    except requests.exceptions.RequestException as e:
        swaparr_logger.error(f"Error fetching queue for {app_name}: {str(e)}")
        return []

def parse_queue_items(records, item_type, app_name):
    """Parse queue items from API response into a standardized format"""
    queue_items = []
    
    for record in records:
        # Extract the name based on the item type
        name = None
        if item_type == "movie" and record.get("movie"):
            name = record["movie"].get("title", "Unknown Movie")
        elif item_type == "series" and record.get("series"):
            name = record["series"].get("title", "Unknown Series")
        elif item_type == "album" and record.get("album"):
            name = record["album"].get("title", "Unknown Album")
        elif item_type == "book" and record.get("book"):
            name = record["book"].get("title", "Unknown Book")
        
        # If no name was found, try to use the download title
        if not name and record.get("title"):
            name = record.get("title", "Unknown Download")
        
        # Parse ETA if available
        eta_seconds = 0
        if record.get("timeleft"):
            eta = record.get("timeleft", "")
            # Basic parsing of timeleft format like "00:30:00" (30 minutes)
            try:
                eta_parts = eta.split(':')
                if len(eta_parts) == 3:
                    eta_seconds = int(eta_parts[0]) * 3600 + int(eta_parts[1]) * 60 + int(eta_parts[2])
            except (ValueError, IndexError):
                eta_seconds = 0
        
        queue_items.append({
            "id": record.get("id"),
            "name": name,
            "size": record.get("size", 0),
            "status": record.get("status", "unknown").lower(),
            "eta": eta_seconds,
            "error_message": record.get("errorMessage", "")
        })
    
    return queue_items

def delete_download(app_name, api_url, api_key, download_id, remove_from_client=True, api_timeout=120):
    """Delete a download from a Starr app"""
    api_version_map = {
        "radarr": "v3",
        "sonarr": "v3",
        "lidarr": "v1",
        "readarr": "v1",
        "whisparr": "v3"
    }
    
    api_version = api_version_map.get(app_name, "v3")
    delete_url = f"{api_url.rstrip('/')}/api/{api_version}/queue/{download_id}?removeFromClient={str(remove_from_client).lower()}&blocklist=true"
    headers = {'X-Api-Key': api_key}
    
    try:
        response = requests.delete(delete_url, headers=headers, timeout=api_timeout)
        response.raise_for_status()
        swaparr_logger.info(f"Successfully removed download {download_id} from {app_name}")
        return True
    except requests.exceptions.RequestException as e:
        swaparr_logger.error(f"Error removing download {download_id} from {app_name}: {str(e)}")
        return False

def process_stalled_downloads(app_name, app_settings, swaparr_settings=None):
    """Process stalled downloads for a specific app instance"""
    if not swaparr_settings:
        swaparr_settings = load_settings("swaparr")
    
    if not swaparr_settings or not swaparr_settings.get("enabled", False):
        swaparr_logger.debug(f"Swaparr is disabled, skipping {app_name} instance: {app_settings.get('instance_name', 'Unknown')}")
        return
    
    swaparr_logger.info(f"Processing stalled downloads for {app_name} instance: {app_settings.get('instance_name', 'Unknown')}")
    
    # Get settings
    max_strikes = swaparr_settings.get("max_strikes", 3)
    max_download_time = parse_time_string_to_seconds(swaparr_settings.get("max_download_time", "2h"))
    ignore_above_size = parse_size_string_to_bytes(swaparr_settings.get("ignore_above_size", "25GB"))
    remove_from_client = swaparr_settings.get("remove_from_client", True)
    dry_run = swaparr_settings.get("dry_run", False)
    
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 120)
    
    if not api_url or not api_key:
        swaparr_logger.error(f"Missing API URL or API Key for {app_name} instance: {app_settings.get('instance_name', 'Unknown')}")
        return
    
    # Load existing strike data
    strike_data = load_strike_data(app_name)
    
    # Get current queue items
    queue_items = get_queue_items(app_name, api_url, api_key, api_timeout)
    
    if not queue_items:
        swaparr_logger.info(f"No queue items found for {app_name} instance: {app_settings.get('instance_name', 'Unknown')}")
        return
    
    # Keep track of items still in queue for cleanup
    current_item_ids = set(item["id"] for item in queue_items)
    
    # Clean up items that are no longer in the queue
    for item_id in list(strike_data.keys()):
        if int(item_id) not in current_item_ids:
            swaparr_logger.debug(f"Removing item {item_id} from strike list as it's no longer in the queue")
            del strike_data[item_id]
    
    # Process each queue item
    for item in queue_items:
        item_id = str(item["id"])
        item_state = "Normal"
        
        # Skip large files if configured
        if item["size"] >= ignore_above_size:
            swaparr_logger.debug(f"Ignoring large download: {item['name']} ({item['size']} bytes > {ignore_above_size} bytes)")
            item_state = "Ignored (Size)"
            continue
        
        # Skip queued or delayed items
        if item["status"] in ["queued", "delay"]:
            swaparr_logger.debug(f"Ignoring {item['status']} download: {item['name']}")
            item_state = f"Ignored ({item['status'].capitalize()})"
            continue
        
        # Initialize strike count if not already in strike data
        if item_id not in strike_data:
            strike_data[item_id] = {
                "strikes": 0,
                "name": item["name"],
                "first_strike_time": None,
                "last_strike_time": None
            }
        
        # Check if download should be striked
        should_strike = False
        
        # Strike if metadata, eta too long, or no progress (eta = 0 and not queued)
        if "metadata" in item["status"].lower() or "metadata" in item["error_message"].lower():
            should_strike = True
            strike_reason = "Metadata"
        elif item["eta"] >= max_download_time:
            should_strike = True
            strike_reason = "ETA too long"
        elif item["eta"] == 0 and item["status"] not in ["queued", "delay"]:
            should_strike = True
            strike_reason = "No progress"
        
        # If we should strike this item, add a strike
        if should_strike:
            strike_data[item_id]["strikes"] += 1
            strike_data[item_id]["last_strike_time"] = datetime.utcnow().isoformat()
            
            if strike_data[item_id]["first_strike_time"] is None:
                strike_data[item_id]["first_strike_time"] = datetime.utcnow().isoformat()
            
            current_strikes = strike_data[item_id]["strikes"]
            swaparr_logger.info(f"Added strike ({current_strikes}/{max_strikes}) to {item['name']} - Reason: {strike_reason}")
            
            # If max strikes reached, remove the download
            if current_strikes >= max_strikes:
                swaparr_logger.warning(f"Max strikes reached for {item['name']}, removing download")
                
                if not dry_run:
                    if delete_download(app_name, api_url, api_key, item["id"], remove_from_client, api_timeout):
                        swaparr_logger.info(f"Successfully removed {item['name']} after {max_strikes} strikes")
                        # Keep the item in strike data for reference but mark as removed
                        strike_data[item_id]["removed"] = True
                        strike_data[item_id]["removed_time"] = datetime.utcnow().isoformat()
                else:
                    swaparr_logger.info(f"DRY RUN: Would have removed {item['name']} after {max_strikes} strikes")
                
                item_state = "Removed" if not dry_run else "Would Remove (Dry Run)"
            else:
                item_state = f"Striked ({current_strikes}/{max_strikes})"
        
        swaparr_logger.debug(f"Processed download: {item['name']} - State: {item_state}")
    
    # Save updated strike data
    save_strike_data(app_name, strike_data)
    
    swaparr_logger.info(f"Finished processing stalled downloads for {app_name} instance: {app_settings.get('instance_name', 'Unknown')}")
