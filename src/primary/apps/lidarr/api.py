#!/usr/bin/env python3
"""
Lidarr-specific API functions
Handles all communication with the Lidarr API
"""

import requests
import json
import time
import datetime
from typing import List, Dict, Any, Optional, Union
from src.primary.utils.logger import get_logger

# Get app-specific logger
logger = get_logger("lidarr")

# Use a session for better performance
session = requests.Session()

# Default API timeout in seconds
API_TIMEOUT = 30

def arr_request(endpoint: str, method: str = "GET", data: Dict = None, app_type: str = "lidarr") -> Any:
    """
    Make a request to the Lidarr API.
    
    Args:
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        app_type: The app type (always lidarr for this module)
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    from src.primary import settings_manager
    api_url = settings_manager.get_setting(app_type, "api_url")
    api_key = settings_manager.get_setting(app_type, "api_key")
    
    if not api_url or not api_key:
        logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Determine the API version
    api_base = "api/v1"  # Lidarr uses v1
    
    # Full URL
    url = f"{api_url}/{api_base}/{endpoint}"
    
    # Headers
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = session.get(url, headers=headers, timeout=API_TIMEOUT)
        elif method == "POST":
            response = session.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
        elif method == "PUT":
            response = session.put(url, headers=headers, json=data, timeout=API_TIMEOUT)
        elif method == "DELETE":
            response = session.delete(url, headers=headers, timeout=API_TIMEOUT)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for errors
        response.raise_for_status()
        
        # Parse JSON response
        if response.text:
            return response.json()
        return {}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def get_download_queue_size() -> int:
    """
    Get the current size of the download queue.
    
    Returns:
        The number of items in the download queue, or 0 if the request failed
    """
    response = arr_request("queue")
    if response and "totalRecords" in response:
        return response["totalRecords"]
    return 0

def get_albums_with_missing_tracks() -> List[Dict]:
    """
    Get a list of albums with missing tracks (not downloaded/available).
    
    Returns:
        A list of album objects with missing tracks
    """
    # Get all albums with detailed information
    albums = arr_request("album")
    if not albums:
        return []
    
    # Filter for albums with missing tracks
    missing_albums = []
    for album in albums:
        # Check if album has missing tracks and is monitored
        if album.get("monitored", False) and album.get("statistics", {}).get("trackCount", 0) > album.get("statistics", {}).get("trackFileCount", 0):
            missing_albums.append(album)
    
    return missing_albums

def get_cutoff_unmet_albums() -> List[Dict]:
    """
    Get a list of albums that don't meet their quality profile cutoff.
    
    Returns:
        A list of album objects that need quality upgrades
    """
    # The cutoffUnmet endpoint in Lidarr
    params = "cutoffUnmet=true"
    albums = arr_request(f"wanted/cutoff?{params}")
    if not albums or "records" not in albums:
        return []
    
    return albums.get("records", [])

def refresh_artist(artist_id: int) -> bool:
    """
    Refresh an artist in Lidarr.
    
    Args:
        artist_id: The ID of the artist to refresh
        
    Returns:
        True if the refresh was successful, False otherwise
    """
    endpoint = f"command"
    data = {
        "name": "RefreshArtist",
        "artistId": artist_id
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Refreshed artist ID {artist_id}")
        return True
    return False

def album_search(album_ids: List[int]) -> bool:
    """
    Trigger a search for one or more albums.
    
    Args:
        album_ids: A list of album IDs to search for
        
    Returns:
        True if the search command was successful, False otherwise
    """
    endpoint = "command"
    data = {
        "name": "AlbumSearch",
        "albumIds": album_ids
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Triggered search for album IDs: {album_ids}")
        return True
    return False