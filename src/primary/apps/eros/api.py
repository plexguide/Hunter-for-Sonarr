#!/usr/bin/env python3
"""
Eros-specific API functions
Handles all communication with the Eros API

Exclusively uses the Eros API v3
"""

import requests
import json
import time
import datetime
import traceback
import sys
from typing import List, Dict, Any, Optional, Union
from src.primary.utils.logger import get_logger

# Get logger for the Eros app
eros_logger = get_logger("eros")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """
    Make a request to the Eros API.
    
    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    if not api_url or not api_key:
        eros_logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Always use v3 API path
    api_base = "api/v3"
    eros_logger.debug(f"Using Eros API path: {api_base}")
    
    # Full URL - ensure no double slashes
    url = f"{api_url.rstrip('/')}/{api_base}/{endpoint.lstrip('/')}"
    
    # Add debug logging for the exact URL being called
    eros_logger.debug(f"Making {method} request to: {url}")
    
    # Headers with User-Agent to identify Huntarr
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": "Huntarr/1.0 (https://github.com/plexguide/Huntarr.io)"
    }
    
    eros_logger.debug(f"Using User-Agent: {headers['User-Agent']}")
    
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
            eros_logger.error(f"Unsupported HTTP method: {method}")
            return None
            
        # Check if the request was successful
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            eros_logger.error(f"Error during {method} request to {endpoint}: {e}, Status Code: {response.status_code}")
            eros_logger.debug(f"Response content: {response.text[:200]}")
            return None
            
        # Try to parse JSON response
        try:
            if response.text:
                result = response.json()
                eros_logger.debug(f"Response from {response.url}: Status {response.status_code}, JSON parsed successfully")
                return result
            else:
                eros_logger.debug(f"Response from {response.url}: Status {response.status_code}, Empty response")
                return {}
        except json.JSONDecodeError:
            eros_logger.error(f"Invalid JSON response from API: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        eros_logger.error(f"Request failed: {e}")
        return None
    except Exception as e:
        eros_logger.error(f"Unexpected error during API request: {e}")
        return None

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int) -> int:
    """
    Get the current size of the download queue.

    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request

    Returns:
        The number of items in the download queue, or -1 if the request failed
    """
    response = arr_request(api_url, api_key, api_timeout, "queue")
    
    if response is None:
        return -1
    
    # V3 API returns a list directly
    if isinstance(response, list):
        return len(response)
    # Fallback to records format if needed
    elif isinstance(response, dict) and "records" in response:
        return len(response["records"])
    else:
        return -1

def get_items_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, search_mode: str = "movie") -> List[Dict[str, Any]]:
    """
    Get a list of items with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.
        search_mode: The search mode to use - 'movie' for movie-based or 'scene' for scene-based

    Returns:
        A list of item objects with missing files, or None if the request failed.
    """
    try:
        eros_logger.debug(f"Retrieving missing items using search mode: {search_mode}...")
        
        if search_mode == "movie":
            # In movie mode, we get all movies and filter for ones without files
            endpoint = "movie"
            
            response = arr_request(api_url, api_key, api_timeout, endpoint)
            
            if response is None:
                return None
            
            # Extract the movies with missing files
            items = []
            if isinstance(response, list):
                # Filter for movies that don't have files (hasFile = false)
                items = [item for item in response if not item.get("hasFile", True)]
            elif isinstance(response, dict) and "records" in response:
                # Fallback to old format if somehow it returns in this format
                items = [item for item in response["records"] if not item.get("hasFile", True)]
        
        elif search_mode == "scene":
            # In scene mode, we try to use scene-specific endpoints
            # First check if the movie-scene endpoint exists
            endpoint = "scene/missing?pageSize=1000"
            
            response = arr_request(api_url, api_key, api_timeout, endpoint)
            
            if response is None:
                # Fallback to regular movie filtering if scene endpoint doesn't exist
                eros_logger.warning("Scene endpoint not available, falling back to movie mode")
                return get_items_with_missing(api_url, api_key, api_timeout, monitored_only, "movie")
            
            # Extract the scenes
            items = []
            if isinstance(response, dict) and "records" in response:
                items = response["records"]
            elif isinstance(response, list):
                items = response
        
        else:
            # Invalid search mode
            eros_logger.error(f"Invalid search mode: {search_mode}. Must be 'movie' or 'scene'")
            return None
        
        # Filter monitored if needed
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
        
        eros_logger.debug(f"Found {len(items)} missing items using {search_mode} mode")
        
        return items
        
    except Exception as e:
        eros_logger.error(f"Error retrieving missing items: {str(e)}")
        return None

def get_cutoff_unmet_items(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """
    Get a list of items that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.

    Returns:
        A list of item objects that need quality upgrades, or None if the request failed.
    """
    try:
        eros_logger.debug(f"Retrieving cutoff unmet items...")
        
        # Endpoint
        endpoint = "wanted/cutoff?pageSize=1000&sortKey=airDateUtc&sortDirection=descending"
        
        response = arr_request(api_url, api_key, api_timeout, endpoint)
        
        if response is None:
            return None
        
        # Extract the episodes/items
        items = []
        if isinstance(response, dict) and "records" in response:
            items = response["records"]
        elif isinstance(response, list):
            items = response
        
        eros_logger.debug(f"Found {len(items)} cutoff unmet items")
        
        # Just filter monitored if needed
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
            eros_logger.debug(f"Found {len(items)} cutoff unmet items after filtering monitored")
        
        return items
        
    except Exception as e:
        eros_logger.error(f"Error retrieving cutoff unmet items: {str(e)}")
        return None

def get_quality_upgrades(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, search_mode: str = "movie") -> List[Dict[str, Any]]:
    """
    Get a list of items that can be upgraded to better quality.

    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored items.
        search_mode: The search mode to use - 'movie' for movie-based or 'scene' for scene-based

    Returns:
        A list of item objects that need quality upgrades, or None if the request failed.
    """
    try:
        eros_logger.debug(f"Retrieving quality upgrade items using search mode: {search_mode}...")
        
        if search_mode == "movie":
            # In movie mode, we get all movies and filter for ones that have files but need quality upgrades
            endpoint = "movie"
            
            response = arr_request(api_url, api_key, api_timeout, endpoint)
            
            if response is None:
                return None
            
            # Extract movies that have files but need quality upgrades
            items = []
            if isinstance(response, list):
                # Filter for movies that have files but haven't met quality cutoff
                items = [item for item in response if item.get("hasFile", False) and item.get("qualityCutoffNotMet", False)]
            elif isinstance(response, dict) and "records" in response:
                # Fallback to old format if somehow it returns in this format
                items = [item for item in response["records"] if item.get("hasFile", False) and item.get("qualityCutoffNotMet", False)]
        
        elif search_mode == "scene":
            # In scene mode, try to use scene-specific endpoints
            endpoint = "scene/cutoff?pageSize=1000"
            
            response = arr_request(api_url, api_key, api_timeout, endpoint)
            
            if response is None:
                # Fallback to regular movie filtering if scene endpoint doesn't exist
                eros_logger.warning("Scene cutoff endpoint not available, falling back to movie mode")
                return get_quality_upgrades(api_url, api_key, api_timeout, monitored_only, "movie")
            
            # Extract the scenes
            items = []
            if isinstance(response, dict) and "records" in response:
                items = response["records"]
            elif isinstance(response, list):
                items = response
                
        else:
            # Invalid search mode
            eros_logger.error(f"Invalid search mode: {search_mode}. Must be 'movie' or 'scene'")
            return None
        
        # Filter monitored if needed
        if monitored_only:
            items = [item for item in items if item.get("monitored", False)]
            
        eros_logger.debug(f"Found {len(items)} quality upgrade items using {search_mode} mode")
        
        return items
        
    except Exception as e:
        eros_logger.error(f"Error retrieving quality upgrade items: {str(e)}")
        return None

def refresh_item(api_url: str, api_key: str, api_timeout: int, item_id: int) -> int:
    """
    Refresh a movie in Whisparr V3.
    
    Args:
        api_url: The base URL of the Whisparr V3 API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_id: The ID of the movie to refresh
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    try:
        eros_logger.info(f"Explicitly refreshing movie with ID {item_id} via API call")
        
        # In Whisparr V3, we use RefreshMovie command directly with the movieId
        payload = {
            "name": "RefreshMovie",
            "movieId": item_id
        }
        
        # Command endpoint
        command_endpoint = "command"
        
        # Make the API request
        response = arr_request(api_url, api_key, api_timeout, command_endpoint, "POST", payload)
        
        if response and "id" in response:
            command_id = response["id"]
            eros_logger.info(f"Refresh movie command triggered with ID {command_id} for movie {item_id}")
            return command_id
        else:
            eros_logger.error(f"Failed to trigger refresh command for movie {item_id} - no command ID returned")
            return None
            
    except Exception as e:
        eros_logger.error(f"Error refreshing movie {item_id}: {str(e)}")
        return None

def item_search(api_url: str, api_key: str, api_timeout: int, item_ids: List[int]) -> int:
    """
    Trigger a search for one or more movies in Whisparr V3.
    
    Args:
        api_url: The base URL of the Whisparr V3 API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        item_ids: A list of movie IDs to search for
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    try:
        if not item_ids:
            eros_logger.warning("No movie IDs provided for search.")
            return None
            
        eros_logger.debug(f"Searching for movies with IDs: {item_ids}")

        # Try several possible command formats, as the API might be in flux
        possible_commands = [
            # Format 1: MoviesSearch with integer IDs (Radarr-like) and no auto-refresh
            {
                "name": "MoviesSearch",
                "movieIds": item_ids,
                "updateScheduledTask": False,
                "runRefreshAfterSearch": False,
                "sendUpdatesToClient": False
            },
            # Format 2: MovieSearch with integer IDs and no auto-refresh
            {
                "name": "MovieSearch",
                "movieIds": item_ids,
                "updateScheduledTask": False,
                "runRefreshAfterSearch": False,
                "sendUpdatesToClient": False
            },
            # Format 3: MoviesSearch with string IDs and no auto-refresh
            {
                "name": "MoviesSearch",
                "movieIds": [str(id) for id in item_ids],
                "updateScheduledTask": False,
                "runRefreshAfterSearch": False,
                "sendUpdatesToClient": False
            },
            # Format 4: MovieSearch with string IDs and no auto-refresh
            {
                "name": "MovieSearch",
                "movieIds": [str(id) for id in item_ids],
                "updateScheduledTask": False,
                "runRefreshAfterSearch": False,
                "sendUpdatesToClient": False
            },
            # Fallback to original formats if the above don't work
            {
                "name": "MoviesSearch",
                "movieIds": item_ids
            },
            {
                "name": "MovieSearch",
                "movieIds": item_ids
            },
            {
                "name": "MoviesSearch",
                "movieIds": [str(id) for id in item_ids]
            },
            {
                "name": "MovieSearch",
                "movieIds": [str(id) for id in item_ids]
            }
        ]
        
        # Command endpoint
        command_endpoint = "command"
        
        # Try each command format until one works
        for i, payload in enumerate(possible_commands):
            eros_logger.debug(f"Trying search command format {i+1}: {payload}")
            
            # Make the API request
            response = arr_request(api_url, api_key, api_timeout, command_endpoint, "POST", payload)
            
            if response and "id" in response:
                command_id = response["id"]
                eros_logger.debug(f"Search command format {i+1} succeeded with ID {command_id}")
                return command_id
                
        # If we've tried all formats and none worked:
        eros_logger.error("All search command formats failed - no command ID returned")
        return None
            
    except Exception as e:
        eros_logger.error(f"Error searching for movies: {str(e)}")
        return None

def get_command_status(api_url: str, api_key: str, api_timeout: int, command_id: int) -> Optional[Dict]:
    """
    Get the status of a specific command.

    Args:
        api_url: The base URL of the Eros API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        command_id: The ID of the command to check

    Returns:
        A dictionary containing the command status, or None if the request failed.
    """
    if not command_id:
        eros_logger.error("No command ID provided for status check.")
        return None
        
    try:
        command_endpoint = f"command/{command_id}"
        
        # Make the API request
        result = arr_request(api_url, api_key, api_timeout, command_endpoint)
        
        if result:
            eros_logger.debug(f"Command {command_id} status: {result.get('status', 'unknown')}")
            return result
        else:
            eros_logger.error(f"Failed to get command status for ID {command_id}")
            return None
            
    except Exception as e:
        eros_logger.error(f"Error getting command status for ID {command_id}: {e}")
        return None

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """
    Check the connection to Whisparr V3 API.
    
    Args:
        api_url: The base URL of the Whisparr V3 API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        
    Returns:
        True if the connection is successful, False otherwise
    """
    try:
        eros_logger.debug(f"Checking connection to Whisparr V3 instance at {api_url}")
        
        endpoint = "system/status"
        response = arr_request(api_url, api_key, api_timeout, endpoint)
        
        if response is not None:
            # Get the version information if available
            version = response.get("version", "unknown")
            
            # Simply check if we received a valid response - Whisparr V3 is in development
            # so the version number might be in various formats
            if version and isinstance(version, str):
                eros_logger.info(f"Successfully connected to Whisparr V3 API, reported version: {version}")
                return True
            else:
                eros_logger.warning(f"Connected to server but found unexpected version format: {version}")
                return False
        else:
            eros_logger.error("Failed to connect to Whisparr V3 API")
            return False
            
    except Exception as e:
        eros_logger.error(f"Error checking connection to Whisparr V3 API: {str(e)}")
        return False
