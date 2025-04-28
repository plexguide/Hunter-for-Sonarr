#!/usr/bin/env python3
"""
Whisparr-specific API functions
Handles all communication with the Whisparr API
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
    Make a request to the Whisparr API.
    
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
    
    # Determine the API version
    api_base = "api/v3"  # Whisparr uses v3 like Radarr
    
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
    if not api_url or not api_key:
        whisparr_logger.error("Whisparr API URL or API Key not provided for queue size check.")
        return -1
    try:
        # Whisparr uses /api/v3/queue like Radarr
        endpoint = f"{api_url.rstrip('/')}/api/v3/queue?page=1&pageSize=1000" # Fetch a large page size
        headers = {"X-Api-Key": api_key}
        response = session.get(endpoint, headers=headers, timeout=api_timeout)
        response.raise_for_status()
        queue_data = response.json()
        queue_size = queue_data.get('totalRecords', 0)
        whisparr_logger.debug(f"Whisparr download queue size: {queue_size}")
        return queue_size
    except requests.exceptions.RequestException as e:
        whisparr_logger.error(f"Error getting Whisparr download queue size: {e}")
        return -1 # Return -1 to indicate an error
    except Exception as e:
        whisparr_logger.error(f"An unexpected error occurred while getting Whisparr queue size: {e}")
        return -1

def get_scenes_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> Optional[List[Dict]]:
    """
    Get a list of scenes with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored scenes.

    Returns:
        A list of scene objects with missing files, or None if the request failed.
    """
    # First, get all series
    series = arr_request(api_url, api_key, api_timeout, "series")
    if series is None:
        whisparr_logger.error("Failed to retrieve series from Whisparr API.")
        return None
    
    if monitored_only:
        # Filter for monitored series only if requested
        series = [s for s in series if s.get("monitored", False)]
    
    # Now get episodes for each series
    all_episodes = []
    for show in series:
        series_id = show.get("id")
        if not series_id:
            continue
            
        # Get episodes for this series
        episodes = arr_request(api_url, api_key, api_timeout, f"episode?seriesId={series_id}")
        if episodes is None:
            whisparr_logger.error(f"Failed to retrieve episodes for series ID {series_id}.")
            continue
            
        # Add series information to each episode for better context
        for episode in episodes:
            episode["series"] = {
                "id": show.get("id"),
                "title": show.get("title", "Unknown"),
                "monitored": show.get("monitored", False)
            }
            
        all_episodes.extend(episodes)
    
    # Filter for missing episodes
    missing_scenes = []
    for scene in all_episodes:
        is_monitored = scene.get("monitored", False)
        has_file = scene.get("hasFile", False)
        # Apply monitored_only filter if requested
        if not has_file and (not monitored_only or is_monitored):
            missing_scenes.append(scene)
    
    whisparr_logger.debug(f"Found {len(missing_scenes)} missing scenes (monitored_only={monitored_only}).")
    return missing_scenes

def get_cutoff_unmet_scenes(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> Optional[List[Dict]]:
    """
    Get a list of scenes that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored scenes.

    Returns:
        A list of scene objects that need quality upgrades, or None if the request failed.
    """
    whisparr_logger.debug("Fetching all series to determine cutoff unmet status...")
    
    # Need quality profile information to determine cutoff unmet status.
    # Fetch quality profiles first.
    profiles = arr_request(api_url, api_key, api_timeout, "qualityprofile")
    if profiles is None:
        whisparr_logger.error("Failed to retrieve quality profiles from Whisparr API.")
        return None
    
    # Create a map for easy lookup: profile_id -> cutoff_format_score (or cutoff quality ID)
    profile_cutoff_map = {p['id']: p.get('cutoff') for p in profiles}
    
    # First, get all series
    series = arr_request(api_url, api_key, api_timeout, "series")
    if series is None:
        whisparr_logger.error("Failed to retrieve series from Whisparr API for cutoff check.")
        return None
    
    if monitored_only:
        # Filter for monitored series only if requested
        series = [s for s in series if s.get("monitored", False)]
    
    # Now get episodes for each series
    all_episodes = []
    for show in series:
        series_id = show.get("id")
        if not series_id:
            continue
            
        # Get episodes for this series
        episodes = arr_request(api_url, api_key, api_timeout, f"episode?seriesId={series_id}")
        if episodes is None:
            whisparr_logger.error(f"Failed to retrieve episodes for series ID {series_id}.")
            continue
            
        # Add series information to each episode for better context
        for episode in episodes:
            episode["series"] = {
                "id": show.get("id"),
                "title": show.get("title", "Unknown"),
                "monitored": show.get("monitored", False)
            }
            
        all_episodes.extend(episodes)

    unmet_scenes = []
    for scene in all_episodes:
        is_monitored = scene.get("monitored", False)
        has_file = scene.get("hasFile", False)
        profile_id = scene.get("qualityProfileId")
        scene_file = scene.get("episodeFile")  # Changed from "sceneFile" to "episodeFile"

        # Apply monitored_only filter if requested
        if not monitored_only or is_monitored:
            if has_file and scene_file and profile_id in profile_cutoff_map:
                cutoff_quality_id = profile_cutoff_map[profile_id]
                current_quality_id = scene_file.get("quality", {}).get("quality", {}).get("id")
                
                # Check if the current quality is below the cutoff
                if current_quality_id is not None and cutoff_quality_id is not None and current_quality_id < cutoff_quality_id:
                    unmet_scenes.append(scene)

    whisparr_logger.debug(f"Found {len(unmet_scenes)} cutoff unmet scenes (monitored_only={monitored_only}).")
    return unmet_scenes

def refresh_scene(api_url: str, api_key: str, api_timeout: int, scene_id: int) -> Optional[int]:
    """
    Refresh a scene in Whisparr.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        scene_id: The ID of the scene to refresh
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    endpoint = "command"
    data = {
        "name": "RefreshEpisode", 
        "episodeIds": [scene_id]
    }
    
    # Use the arr_request function
    response = arr_request(api_url, api_key, api_timeout, endpoint, method="POST", data=data)
    if response and 'id' in response:
        command_id = response['id']
        whisparr_logger.debug(f"Triggered refresh for scene ID {scene_id}. Command ID: {command_id}")
        return command_id
    else:
        whisparr_logger.error(f"Failed to trigger refresh command for scene ID {scene_id}. Response: {response}")
        return None

def scene_search(api_url: str, api_key: str, api_timeout: int, scene_ids: List[int]) -> Optional[int]:
    """
    Trigger a search for one or more scenes.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        scene_ids: A list of scene IDs to search for
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    if not scene_ids:
        whisparr_logger.warning("No scene IDs provided for search.")
        return None
        
    endpoint = "command"
    data = {
        "name": "EpisodeSearch",
        "episodeIds": scene_ids
    }
    
    # Use the arr_request function
    response = arr_request(api_url, api_key, api_timeout, endpoint, method="POST", data=data)
    if response and 'id' in response:
        command_id = response['id']
        whisparr_logger.debug(f"Triggered search for scene IDs: {scene_ids}. Command ID: {command_id}")
        return command_id
    else:
        whisparr_logger.error(f"Failed to trigger search command for scene IDs {scene_ids}. Response: {response}")
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
    endpoint = f"command/{command_id}"
    response = arr_request(api_url, api_key, api_timeout, endpoint, method="GET")
    if response:
        whisparr_logger.debug(f"Checked status for command ID {command_id}. Status: {response.get('status')}")
        return response
    else:
        whisparr_logger.error(f"Failed to get status for command ID {command_id}.")
        return None

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """Check the connection to Whisparr API."""
    try:
        # Ensure api_url is properly formatted
        if not api_url:
            logger.error("API URL is empty or not set")
            return False
            
        # Make sure api_url has a scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
            return False
            
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = api_url.rstrip('/')
        full_url = f"{base_url}/api/v3/system/status"
        
        response = requests.get(full_url, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info("Successfully connected to Whisparr.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Whisparr: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Whisparr connection check: {e}")
        return False