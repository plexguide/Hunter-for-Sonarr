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
    if not api_url or not api_key:
        whisparr_logger.error("Whisparr API URL or API Key not provided for queue size check.")
        return -1
    try:
        # Use the arr_request function to maintain API version compatibility
        endpoint = "queue?page=1&pageSize=1000"  # Fetch a large page size
        queue_data = arr_request(api_url, api_key, api_timeout, endpoint, api_version=api_version)
        if queue_data is None:
            return -1
        
        queue_size = queue_data.get('totalRecords', 0)
        whisparr_logger.debug(f"Whisparr download queue size: {queue_size}")
        return queue_size
    except Exception as e:
        whisparr_logger.error(f"An unexpected error occurred while getting Whisparr queue size: {e}")
        return -1

def get_scenes_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, api_version: str = "v3") -> Optional[List[Dict]]:
    """
    Get a list of scenes with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored scenes.
        api_version: API version to use ("v2" or "v3")

    Returns:
        A list of scene objects with missing files, or None if the request failed.
    """
    whisparr_logger.info(f"Getting scenes with missing files (API version: {api_version})")
    
    # First, get all series
    series = arr_request(api_url, api_key, api_timeout, "series", api_version=api_version)
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
        episodes = arr_request(api_url, api_key, api_timeout, f"episode?seriesId={series_id}", api_version=api_version)
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

def get_cutoff_unmet_scenes(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, api_version: str = "v3") -> Optional[List[Dict]]:
    """
    Get a list of scenes that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored scenes.
        api_version: API version to use ("v2" or "v3")

    Returns:
        A list of scene objects that need quality upgrades, or None if the request failed.
    """
    whisparr_logger.debug(f"Fetching cutoff unmet scenes (API version: {api_version})")
    
    # Need quality profile information to determine cutoff unmet status.
    # Fetch quality profiles first.
    profiles = arr_request(api_url, api_key, api_timeout, "qualityprofile", api_version=api_version)
    if profiles is None:
        whisparr_logger.error("Failed to retrieve quality profiles from Whisparr API.")
        return None
        
    # Create a mapping of profile ID to cutoff information
    profile_cutoffs = {}
    for profile in profiles:
        profile_id = profile.get("id")
        if profile_id is not None:
            if api_version == "v2":
                # In v2, the cutoff is a simple quality ID
                cutoff = profile.get("cutoff")
                profile_cutoffs[profile_id] = cutoff
            else:  # v3
                # In v3, the cutoff is more complex with items
                cutoff = profile.get("cutoff")
                profile_cutoffs[profile_id] = cutoff
    
    # Get all series
    series = arr_request(api_url, api_key, api_timeout, "series", api_version=api_version)
    if series is None:
        whisparr_logger.error("Failed to retrieve series from Whisparr API.")
        return None
    
    # Create a mapping of series ID to quality profile ID
    series_profiles = {}
    for show in series:
        series_id = show.get("id")
        profile_id = show.get("qualityProfileId")
        if series_id and profile_id:
            series_profiles[series_id] = profile_id
    
    # Get episodes with files
    all_episodes_with_files = []
    
    for show in series:
        series_id = show.get("id")
        if not series_id:
            continue
            
        # Skip unmonitored series if monitored_only is True
        if monitored_only and not show.get("monitored", False):
            continue
            
        # Get episodes for this series
        episodes = arr_request(api_url, api_key, api_timeout, f"episode?seriesId={series_id}", api_version=api_version)
        if episodes is None:
            whisparr_logger.error(f"Failed to retrieve episodes for series ID {series_id}.")
            continue
            
        # Add series information to each episode
        for episode in episodes:
            episode["series"] = {
                "id": show.get("id"),
                "title": show.get("title", "Unknown"),
                "monitored": show.get("monitored", False),
                "qualityProfileId": show.get("qualityProfileId")
            }
            
        # Filter for episodes with files
        episodes_with_files = [e for e in episodes if e.get("hasFile", False)]
        all_episodes_with_files.extend(episodes_with_files)
    
    # Find episodes that need quality upgrades
    cutoff_unmet_scenes = []
    
    for scene in all_episodes_with_files:
        # Skip if not monitored and monitored_only is True
        is_monitored = scene.get("monitored", False)
        if monitored_only and not is_monitored:
            continue
            
        series_id = scene.get("series", {}).get("id")
        if not series_id:
            continue
            
        # Get quality profile ID for this series
        profile_id = series_profiles.get(series_id)
        if not profile_id:
            continue
            
        # Check if scene meets cutoff quality
        quality_cutoff = profile_cutoffs.get(profile_id)
        if quality_cutoff is None:
            continue
            
        if api_version == "v2":
            # v2 API has a simpler quality model
            scene_quality_id = scene.get("episodeFile", {}).get("quality", {}).get("quality", {}).get("id")
            if scene_quality_id and scene_quality_id < quality_cutoff:
                cutoff_unmet_scenes.append(scene)
        else:  # v3
            # v3 API has a more complex quality model with items
            scene_quality = scene.get("episodeFile", {}).get("quality")
            
            # Logic for v3 quality check - handling the Eros quality model
            # This is specific to Whisparr v3 (Eros) API which uses a different quality model
            # Typically need to check against cutoff and quality items
            
            # Simplified implementation - this should be customized based on exact API response structure
            if scene_quality:
                quality_meets_cutoff = False
                # Add your v3-specific logic here to determine if quality meets cutoff
                if not quality_meets_cutoff:
                    cutoff_unmet_scenes.append(scene)
    
    whisparr_logger.debug(f"Found {len(cutoff_unmet_scenes)} scenes that need quality upgrades.")
    return cutoff_unmet_scenes

def refresh_scene(api_url: str, api_key: str, api_timeout: int, scene_id: int, api_version: str = "v3") -> Optional[int]:
    """
    Refresh a scene in Whisparr.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        scene_id: The ID of the scene to refresh
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    if not scene_id:
        whisparr_logger.error("No scene ID provided for refresh.")
        return None
        
    try:
        # API endpoint is the same for v2 and v3, just with different base paths
        data = {
            "name": "RefreshEpisode",
            "episodeIds": [scene_id]
        }
        
        result = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=data, api_version=api_version)
        if result and "id" in result:
            command_id = result["id"]
            whisparr_logger.info(f"Successfully triggered refresh for scene ID {scene_id}, command ID: {command_id}")
            return command_id
        else:
            whisparr_logger.error(f"Failed to trigger refresh for scene ID {scene_id}. Response: {result}")
            return None
    except Exception as e:
        whisparr_logger.error(f"Error refreshing scene ID {scene_id}: {e}")
        return None

def scene_search(api_url: str, api_key: str, api_timeout: int, scene_ids: List[int], api_version: str = "v3") -> Optional[int]:
    """
    Trigger a search for one or more scenes.
    
    Args:
        api_url: The base URL of the Whisparr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        scene_ids: A list of scene IDs to search for
        api_version: API version to use ("v2" or "v3")
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    if not scene_ids:
        whisparr_logger.error("No scene IDs provided for search.")
        return None
        
    try:
        # API endpoint is the same for v2 and v3, just with different base paths
        data = {
            "name": "EpisodeSearch",
            "episodeIds": scene_ids
        }
        
        result = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=data, api_version=api_version)
        if result and "id" in result:
            command_id = result["id"]
            whisparr_logger.info(f"Successfully triggered search for scene IDs {scene_ids}, command ID: {command_id}")
            return command_id
        else:
            whisparr_logger.error(f"Failed to trigger search for scene IDs {scene_ids}. Response: {result}")
            return None
    except Exception as e:
        whisparr_logger.error(f"Error searching for scene IDs {scene_ids}: {e}")
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