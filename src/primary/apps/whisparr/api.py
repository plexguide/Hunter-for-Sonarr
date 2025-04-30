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
    
    # IMPORTANT: Whisparr 2.x uses v3 API endpoints even though it's labeled as v2 in our settings
    # Always use v3 for API path
    api_base = f"api/v3"
    whisparr_logger.debug(f"Using Whisparr API base path: {api_base}")
    
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
            
        # Check if the request was successful
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            whisparr_logger.error(f"Error during {method} request to {endpoint}: {e}, Status Code: {response.status_code}")
            return None
            
        # Try to parse JSON response
        try:
            if response.text:
                return response.json()
            else:
                return {}
        except json.JSONDecodeError:
            whisparr_logger.error(f"Invalid JSON response from API: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        whisparr_logger.error(f"Request failed: {e}")
        return None
    except Exception as e:
        whisparr_logger.error(f"Unexpected error during API request: {e}")
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
        whisparr_logger.debug(f"Retrieving missing items...")
        
        # Endpoint parameters - always use v3 format since we're using v3 API
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
        whisparr_logger.debug(f"Retrieving cutoff unmet items...")
        
        # Endpoint - always use v3 format
        endpoint = "wanted/cutoff?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint, api_version=api_version)
        
        if response is None:
            return None
        
        # Extract the episodes/items
        items = []
        if isinstance(response, dict) and "records" in response:
            items = response["records"]
        
        whisparr_logger.debug(f"Found {len(items)} cutoff unmet items")
        
        # Just filter monitored if needed - we're always using v3 API now
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
            whisparr_logger.debug(f"Found {len(items)} cutoff unmet items after filtering monitored")
        
        return items
        
    except Exception as e:
        whisparr_logger.error(f"Error retrieving cutoff unmet items: {str(e)}")
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
        
        # Some Whisparr versions have issues with RefreshEpisode, try a safer approach
        # Use series refresh instead if we can get the series ID from the episode
        # First, attempt to get the episode details
        episode_endpoint = f"episode/{item_id}"
        episode_data = arr_request(api_url, api_key, api_timeout, episode_endpoint, api_version=api_version)
        
        if episode_data and "seriesId" in episode_data:
            # We have the series ID, use series refresh which is more reliable
            series_id = episode_data["seriesId"]
            whisparr_logger.debug(f"Retrieved series ID {series_id} for episode {item_id}, using series refresh")
            
            # RefreshSeries is generally more reliable
            payload = {
                "name": "RefreshSeries",
                "seriesId": series_id
            }
        else:
            # Fall back to episode refresh if we can't get the series ID
            whisparr_logger.debug(f"Could not retrieve series ID for episode {item_id}, using episode refresh")
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
        
        # Always use the same payload format since we're always using v3 API
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
    try:
        # System status is a good endpoint for verifying API connectivity
        response = arr_request(api_url, api_key, api_timeout, "system/status", api_version=api_version)
        
        if response is not None:
            # Get the version information if available
            version = response.get("version", "unknown")
            whisparr_logger.info(f"Successfully connected to Whisparr {version} using API v3")
            return True
        else:
            whisparr_logger.error("Failed to connect to Whisparr API")
            return False
            
    except Exception as e:
        whisparr_logger.error(f"Error checking connection to Whisparr API: {str(e)}")
        return False