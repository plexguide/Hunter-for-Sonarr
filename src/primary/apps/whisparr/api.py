#!/usr/bin/env python3
"""
Whisparr-specific API functions
Handles all communication with the Whisparr API

Exclusively uses the Whisparr V2 API
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

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """
    Make a request to the Whisparr V2 API.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    if not api_url or not api_key:
        whisparr_logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Always use v2 for Whisparr API
    api_base = "api"
    whisparr_logger.debug(f"Using Whisparr V2 API: {api_base}")
    
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

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int) -> int:
    """
    Get the current size of the download queue.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request

    Returns:
        The number of items in the download queue, or -1 if the request failed
    """
    response = arr_request(api_url, api_key, api_timeout, "queue")
    
    if response is None:
        return -1
    
    # V2 API uses records in queue response
    if isinstance(response, dict) and "records" in response:
        return len(response["records"])
    elif isinstance(response, list):
        return len(response)
    else:
        return -1

def get_items_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """
    Get a list of items with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.

    Returns:
        A list of item objects with missing files, or None if the request failed.
    """
    try:
        whisparr_logger.debug(f"Retrieving missing items...")
        
        # Endpoint parameters - always use v2 format
        endpoint = "wanted/missing?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint)
        
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

def get_cutoff_unmet_items(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """
    Get a list of items that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.

    Returns:
        A list of item objects that need quality upgrades, or None if the request failed.
    """
    try:
        whisparr_logger.debug(f"Retrieving cutoff unmet items...")
        
        # Endpoint - always use v2 format
        endpoint = "wanted/cutoff?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint)
        
        if response is None:
            return None
        
        # Extract the episodes/items
        items = []
        if isinstance(response, dict) and "records" in response:
            items = response["records"]
        
        whisparr_logger.debug(f"Found {len(items)} cutoff unmet items")
        
        # Just filter monitored if needed
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
            whisparr_logger.debug(f"Found {len(items)} cutoff unmet items after filtering monitored")
        
        return items
        
    except Exception as e:
        whisparr_logger.error(f"Error retrieving cutoff unmet items: {str(e)}")
        return None

def refresh_item(api_url: str, api_key: str, api_timeout: int, item_id: int) -> int:
    """
    Refresh an item in Whisparr.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_id: The ID of the item to refresh
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    try:
        whisparr_logger.debug(f"Refreshing item with ID {item_id}")
        
        # Some Whisparr versions have issues with RefreshEpisode, try a safer approach
        # Use series refresh instead if we can get the series ID from the episode
        # First, attempt to get the episode details
        episode_endpoint = f"episode/{item_id}"
        episode_data = arr_request(api_url, api_key, api_timeout, episode_endpoint)
        
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
        
        response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload)
        
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

def item_search(api_url: str, api_key: str, api_timeout: int, item_ids: List[int]) -> int:
    """
    Trigger a search for one or more items.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_ids: A list of item IDs to search for
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    try:
        whisparr_logger.debug(f"Searching for items with IDs: {item_ids}")
        
        # Always use the same payload format since we're always using v2 API
        payload = {
            "name": "EpisodeSearch",
            "episodeIds": item_ids
        }
        
        response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload)
        
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

def get_command_status(api_url: str, api_key: str, api_timeout: int, command_id: int) -> Optional[Dict]:
    """
    Get the status of a specific command.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        command_id: The ID of the command to check

    Returns:
        A dictionary containing the command status, or None if the request failed.
    """
    if not command_id:
        whisparr_logger.error("No command ID provided for status check.")
        return None
        
    try:
        endpoint = f"command/{command_id}"
        result = arr_request(api_url, api_key, api_timeout, endpoint)
        
        if result:
            whisparr_logger.debug(f"Command {command_id} status: {result.get('status', 'unknown')}")
            return result
        else:
            whisparr_logger.error(f"Failed to get status for command ID {command_id}")
            return None
    except Exception as e:
        whisparr_logger.error(f"Error getting command status for ID {command_id}: {e}")
        return None

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """
    Check the connection to Whisparr API.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        
    Returns:
        True if the connection is successful, False otherwise
    """
    try:
        # System status is a good endpoint for verifying API connectivity
        response = arr_request(api_url, api_key, api_timeout, "system/status")
        
        if response is not None:
            # Get the version information if available
            version = response.get("version", "unknown")
            whisparr_logger.info(f"Successfully connected to Whisparr {version} using API v2")
            return True
        else:
            whisparr_logger.error("Failed to connect to Whisparr API")
            return False
            
    except Exception as e:
        whisparr_logger.error(f"Error checking connection to Whisparr API: {str(e)}")
        return False