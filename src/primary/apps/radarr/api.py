#!/usr/bin/env python3
"""
Radarr-specific API functions
Handles all communication with the Radarr API
"""

import requests
import json
import time
import datetime
from typing import List, Dict, Any, Optional, Union
from primary.utils.logger import get_logger

# Get app-specific logger
logger = get_logger("radarr")

# Use a session for better performance
session = requests.Session()

# Default API timeout in seconds
API_TIMEOUT = 30

def arr_request(endpoint: str, method: str = "GET", data: Dict = None, app_type: str = "radarr") -> Any:
    """
    Make a request to the Radarr API.
    
    Args:
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        app_type: The app type (always radarr for this module)
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    from primary import keys_manager
    api_url, api_key = keys_manager.get_api_keys(app_type)
    
    if not api_url or not api_key:
        logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Determine the API version
    api_base = "api/v3"  # Radarr uses v3
    
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

def get_movies_with_missing() -> List[Dict]:
    """
    Get a list of movies with missing files (not downloaded/available).
    
    Returns:
        A list of movie objects with missing files
    """
    movies = arr_request("movie")
    if not movies:
        return []
    
    missing_movies = []
    for movie in movies:
        if not movie.get("hasFile", False) and movie.get("monitored", False):
            missing_movies.append(movie)
    
    return missing_movies

def get_cutoff_unmet_movies() -> List[Dict]:
    """
    Get a list of movies that don't meet their quality profile cutoff.
    
    Returns:
        A list of movie objects that need quality upgrades
    """
    params = "cutoffUnmet=true"
    movies = arr_request(f"movie?{params}")
    if not movies:
        return []
    
    # Filter to only include movies that have a file but need an upgrade
    unmet_movies = []
    for movie in movies:
        if movie.get("hasFile", False) and movie.get("monitored", False):
            unmet_movies.append(movie)
    
    return unmet_movies

def refresh_movie(movie_id: int) -> bool:
    """
    Refresh a movie in Radarr.
    
    Args:
        movie_id: The ID of the movie to refresh
        
    Returns:
        True if the refresh was successful, False otherwise
    """
    endpoint = f"command"
    data = {
        "name": "RefreshMovie",
        "movieIds": [movie_id]
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Refreshed movie ID {movie_id}")
        return True
    return False

def movie_search(movie_ids: List[int]) -> bool:
    """
    Trigger a search for one or more movies.
    
    Args:
        movie_ids: A list of movie IDs to search for
        
    Returns:
        True if the search command was successful, False otherwise
    """
    endpoint = "command"
    data = {
        "name": "MoviesSearch",
        "movieIds": movie_ids
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Triggered search for movie IDs: {movie_ids}")
        return True
    return False