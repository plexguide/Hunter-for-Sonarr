#!/usr/bin/env python3
"""
Whisparr-specific API functions
Handles all communication with the Whisparr API

Supports both v2 (legacy) and v3 (Eros) API versions
"""

import requests
import json
import time
import datetime
import traceback
import sys
from typing import List, Dict, Any, Optional, Union
from src.primary.utils.logger import get_logger

# Get logger for the Whisparr app
whisparr_logger = get_logger("whisparr")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None, api_version: str = "v3") -> Any:
    """
    Make a request to the Whisparr API.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    if not api_url or not api_key:
        whisparr_logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Determine the API version
    api_base = f"api/{api_version}"
    whisparr_logger.debug(f"Using Whisparr API version: {api_version}")
    
    # Full URL - ensure no double slashes
    url = f"{api_url.rstrip('/')}/{api_base}/{endpoint.lstrip('/')}"
    
    # Headers
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = session.get(url, headers=headers, timeout=api_timeout)
        elif method == "POST":
            response = session.post(url, headers=headers, json=data, timeout=api_timeout)
        elif method == "PUT":
            response = session.put(url, headers=headers, json=data, timeout=api_timeout)
        elif method == "DELETE":
            response = session.delete(url, headers=headers, timeout=api_timeout)
        else:
            whisparr_logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for errors
        response.raise_for_status()
        
        # Parse JSON response
        if response.text:
            return response.json()
        return {}
        
    except requests.exceptions.RequestException as e:
        # Add detailed error logging
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_details += f", Status Code: {e.response.status_code}"
            if e.response.content:
                error_details += f", Content: {e.response.content[:200]}"
        whisparr_logger.error(f"Error during {method} request to {endpoint}: {error_details}")
        return None
    except Exception as e:
        # Catch all exceptions and log them with traceback
        error_msg = f"CRITICAL ERROR in Whisparr arr_request: {str(e)}"
        whisparr_logger.error(error_msg)
        whisparr_logger.error(f"Full traceback: {traceback.format_exc()}")
        print(error_msg, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int, api_version: str = "v3") -> int:
    """
    Get the current size of the download queue.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        api_version: API version to use ("v2" or "v3")

    Returns:
        The number of items in the download queue, or -1 if the request failed
    """
    response = arr_request(api_url, api_key, api_timeout, "queue", api_version=api_version)
    
    if response is None:
        return -1
    
    # V2 and V3 both use records in queue response, but sometimes the structure is different
    if isinstance(response, dict) and "records" in response:
        return len(response["records"])
    elif isinstance(response, list):
        return len(response)
    else:
        return -1

def get_items_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, api_version: str = "v3") -> List[Dict[str, Any]]:
    """
    Get a list of items with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.
        api_version: API version to use ("v2" or "v3")

    Returns:
        A list of item objects with missing files, or None if the request failed.
    """
    try:
        whisparr_logger.debug(f"Retrieving missing items with API version {api_version}")
        
        # Endpoint differs by API version
        if api_version == "v2":
            endpoint = "wanted/missing?pageSize=1000&sortKey=airDateUtc&sortDir=desc"
        else:  # v3/Eros
            endpoint = "wanted/missing?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint, api_version=api_version)
        
        if response is None:
            return None
        
        # Extract the episodes/items
        items = []
        if isinstance(response, dict) and "records" in response:
            items = response["records"]
        
        # Filter monitored if needed
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
        
        whisparr_logger.debug(f"Found {len(items)} missing items")
        return items
        
    except Exception as e:
        whisparr_logger.error(f"Error retrieving missing items: {str(e)}")
        return None

def get_cutoff_unmet_items(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, api_version: str = "v3") -> List[Dict[str, Any]]:
    """
    Get a list of items that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.
        api_version: API version to use ("v2" or "v3")

    Returns:
        A list of item objects that need quality upgrades, or None if the request failed.
    """
    try:
        whisparr_logger.debug(f"Retrieving cutoff unmet items with API version {api_version}")
        
        # Endpoint differs by API version
        if api_version == "v2":
            endpoint = "wanted/cutoff?pageSize=1000&sortKey=airDateUtc&sortDir=desc"
        else:  # v3/Eros
            endpoint = "wanted/cutoff?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint, api_version=api_version)
        
        if response is None:
            return None
        
        # Extract the episodes/items
        items = []
        if isinstance(response, dict) and "records" in response:
            items = response["records"]
        
        whisparr_logger.debug(f"Found {len(items)} cutoff unmet items")
        
        # For v2, we need to filter out items where qualityCutoffNotMet is False
        # For v3, we can just use the API's filtering which already returns appropriate results
        if api_version == "v2":
            # Get quality profiles
            profiles_response = arr_request(api_url, api_key, api_timeout, "profile", api_version=api_version)
            if not profiles_response:
                whisparr_logger.error("Failed to retrieve quality profiles")
                return None
            
            # Create a lookup for profile qualities
            profiles_lookup = {}
            for profile in profiles_response:
                profile_id = profile.get("id")
                if profile_id is not None:
                    cutoff = profile.get("cutoff")
                    qualities = profile.get("items", [])
                    allowed_qualities = []
                    for quality in qualities:
                        if quality.get("allowed", False):
                            if "quality" in quality:
                                allowed_qualities.append(quality["quality"])
                            else:
                                allowed_qualities.extend([q for q in quality.get("qualities", [])])
                    
                    profiles_lookup[profile_id] = {
                        "cutoff": cutoff,
                        "qualities": allowed_qualities
                    }
            
            # Filter items that need quality upgrade
            filtered_items = []
            for item in items:
                if monitored_only and not item.get("monitored", False):
                    continue
                
                # Get the item's quality and profile
                quality_info = item.get("episodeFile", {}).get("quality", {}) if "episodeFile" in item else None
                if not quality_info:
                    continue
                
                quality_id = quality_info.get("quality", {}).get("id") if "quality" in quality_info else None
                profile_id = item.get("series", {}).get("profileId") if "series" in item else None
                
                if quality_id is None or profile_id is None:
                    continue
                
                # Check if item meets cutoff
                profile = profiles_lookup.get(profile_id)
                if not profile:
                    continue
                
                # Check if current quality is below cutoff
                if profile["cutoff"] is not None:
                    cutoff_met = False
                    for quality in profile["qualities"]:
                        if quality.get("id") == quality_id:
                            cutoff_met = True
                            break
                        if quality.get("id") == profile["cutoff"]:
                            break
                    
                    if not cutoff_met:
                        filtered_items.append(item)
            
            items = filtered_items
            whisparr_logger.debug(f"Found {len(items)} items that don't meet cutoff quality after filtering")
        else:  # For v3, just filter monitored if needed
            if monitored_only:
                items = [item for item in items if item.get("monitored", False)]
            whisparr_logger.debug(f"Found {len(items)} cutoff unmet items after filtering monitored")
        
        return items
        
    except Exception as e:
        whisparr_logger.error(f"Error retrieving cutoff unmet items: {str(e)}")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        whisparr_logger.debug("".join(tb_lines))
        return None

def refresh_item(api_url: str, api_key: str, api_timeout: int, item_id: int, api_version: str = "v3") -> int:
    """
    Refresh an item in Whisparr.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_id: The ID of the item to refresh
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    try:
        whisparr_logger.debug(f"Refreshing item with ID {item_id}")
        
        # Different payload for different API versions
        if api_version == "v2":
            payload = {
                "name": "RefreshEpisode",
                "episodeIds": [item_id]
            }
        else:  # v3/Eros
            payload = {
                "name": "RefreshEpisode",
                "episodeIds": [item_id]
            }
        
        response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload, api_version=api_version)
        
        if response and "id" in response:
            command_id = response["id"]
            whisparr_logger.debug(f"Refresh command triggered with ID {command_id}")
            return command_id
        else:
            whisparr_logger.error("Failed to trigger refresh command")
            return None
            
    except Exception as e:
        whisparr_logger.error(f"Error refreshing item: {str(e)}")
        return None

def item_search(api_url: str, api_key: str, api_timeout: int, item_ids: List[int], api_version: str = "v3") -> int:
    """
    Trigger a search for one or more items.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_ids: A list of item IDs to search for
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    try:
        whisparr_logger.debug(f"Searching for items with IDs: {item_ids}")
        
        # Both API versions use the same command structure
        payload = {
            "name": "EpisodeSearch",
            "episodeIds": item_ids
        }
        
        response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload, api_version=api_version)
        
        if response and "id" in response:
            command_id = response["id"]
            whisparr_logger.debug(f"Search command triggered with ID {command_id}")
            return command_id
        else:
            whisparr_logger.error("Failed to trigger search command")
            return None
            
    except Exception as e:
        whisparr_logger.error(f"Error searching for items: {str(e)}")
        return None

def get_command_status(api_url: str, api_key: str, api_timeout: int, command_id: int, api_version: str = "v3") -> Optional[Dict]:
    """
    Get the status of a specific command.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        command_id: The ID of the command to check
        api_version: API version to use ("v2" or "v3")

    Returns:
        A dictionary containing the command status, or None if the request failed.
    """
    if not command_id:
        whisparr_logger.error("No command ID provided for status check.")
        return None
        
    try:
        endpoint = f"command/{command_id}"
        result = arr_request(api_url, api_key, api_timeout, endpoint, api_version=api_version)
        
        if result:
            whisparr_logger.debug(f"Command {command_id} status: {result.get('status', 'unknown')}")
            return result
        else:
            whisparr_logger.error(f"Failed to get status for command ID {command_id}")
            return None
    except Exception as e:
        whisparr_logger.error(f"Error getting command status for ID {command_id}: {e}")
        return None

def check_connection(api_url: str, api_key: str, api_timeout: int, api_version: str = "v3") -> bool:
    """
    Check the connection to Whisparr API.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        True if the connection is successful, False otherwise
    """
    whisparr_logger.info(f"Checking connection to Whisparr (API version: {api_version})...")
    
    if not api_url or not api_key:
        whisparr_logger.error("API URL or API key is not provided")
        return False
        
    try:
        # Use system/status endpoint which is available in both v2 and v3
        result = arr_request(api_url, api_key, api_timeout, "system/status", api_version=api_version)
        
        if result:
            version = result.get("version", "Unknown")
            app_name = result.get("appName", "Whisparr")
            whisparr_logger.info(f"Successfully connected to {app_name} {version} using API v{api_version}")
            return True
        else:
            whisparr_logger.error(f"Failed to connect to Whisparr API v{api_version}")
            return False
    except Exception as e:
        whisparr_logger.error(f"Error checking connection to Whisparr: {e}")
        return False