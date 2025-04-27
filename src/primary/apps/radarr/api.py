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
# Correct the import path
from src.primary.utils.logger import get_logger

# Get logger for the Radarr app
radarr_logger = get_logger("radarr")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """
    Make a request to the Radarr API.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    if not api_url or not api_key:
        radarr_logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Determine the API version
    api_base = "api/v3"  # Radarr uses v3
    
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
            radarr_logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for errors
        response.raise_for_status()
        
        # Parse JSON response
        if response.text:
            return response.json()
        return {}
        
    except requests.exceptions.RequestException as e:
        radarr_logger.error(f"API request failed: {e}")
        return None

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int) -> int:
    """
    Get the current size of the download queue.

    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request

    Returns:
        The number of items in the download queue, or -1 if the request failed
    """
    if not api_url or not api_key:
        radarr_logger.error("Radarr API URL or API Key not provided for queue size check.")
        return -1
    try:
        # Radarr uses /api/v3/queue
        endpoint = f"{api_url.rstrip('/')}/api/v3/queue?page=1&pageSize=1000" # Fetch a large page size
        headers = {"X-Api-Key": api_key}
        response = session.get(endpoint, headers=headers, timeout=api_timeout)
        response.raise_for_status()
        queue_data = response.json()
        queue_size = queue_data.get('totalRecords', 0)
        radarr_logger.debug(f"Radarr download queue size: {queue_size}")
        return queue_size
    except requests.exceptions.RequestException as e:
        radarr_logger.error(f"Error getting Radarr download queue size: {e}")
        return -1 # Return -1 to indicate an error
    except Exception as e:
        radarr_logger.error(f"An unexpected error occurred while getting Radarr queue size: {e}")
        return -1

def get_movies_with_missing(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> Optional[List[Dict]]:
    """
    Get a list of movies with missing files (not downloaded/available).

    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored movies.

    Returns:
        A list of movie objects with missing files, or None if the request failed.
    """
    # Use the updated arr_request with passed arguments
    movies = arr_request(api_url, api_key, api_timeout, "movie")
    if movies is None: # Check for None explicitly, as an empty list is valid
        radarr_logger.error("Failed to retrieve movies from Radarr API.")
        return None
    
    missing_movies = []
    for movie in movies:
        is_monitored = movie.get("monitored", False)
        has_file = movie.get("hasFile", False)
        # Apply monitored_only filter if requested
        if not has_file and (not monitored_only or is_monitored):
            missing_movies.append(movie)
    
    radarr_logger.debug(f"Found {len(missing_movies)} missing movies (monitored_only={monitored_only}).")
    return missing_movies

def get_cutoff_unmet_movies(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> Optional[List[Dict]]:
    """
    Get a list of movies that don't meet their quality profile cutoff.

    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored movies.

    Returns:
        A list of movie objects that need quality upgrades, or None if the request failed.
    """
    # Radarr API endpoint for cutoff unmet movies
    # Note: Radarr's /api/v3/movie endpoint doesn't directly support a simple 'cutoffUnmet=true' like Sonarr's wanted/cutoff.
    # We need to fetch all movies and filter locally, or use the /api/v3/movie/lookup endpoint if searching by TMDB/IMDB ID.
    # Fetching all movies is simpler for now.
    radarr_logger.debug("Fetching all movies to determine cutoff unmet status...")
    movies = arr_request(api_url, api_key, api_timeout, "movie")
    if movies is None:
        radarr_logger.error("Failed to retrieve movies from Radarr API for cutoff check.")
        return None

    # Need quality profile information to determine cutoff unmet status.
    # Fetch quality profiles first.
    profiles = arr_request(api_url, api_key, api_timeout, "qualityprofile")
    if profiles is None:
        radarr_logger.error("Failed to retrieve quality profiles from Radarr API.")
        return None
    
    # Create a map for easy lookup: profile_id -> cutoff_format_score (or cutoff quality ID)
    # Radarr profiles have 'cutoff' (quality ID) and potentially 'cutoffFormatScore'
    profile_cutoff_map = {p['id']: p.get('cutoff') for p in profiles}
    # TODO: Potentially incorporate cutoffFormatScore if needed for more complex logic

    unmet_movies = []
    for movie in movies:
        is_monitored = movie.get("monitored", False)
        has_file = movie.get("hasFile", False)
        profile_id = movie.get("qualityProfileId")
        movie_file = movie.get("movieFile")

        # Apply monitored_only filter if requested
        if not monitored_only or is_monitored:
            if has_file and movie_file and profile_id in profile_cutoff_map:
                cutoff_quality_id = profile_cutoff_map[profile_id]
                current_quality_id = movie_file.get("quality", {}).get("quality", {}).get("id")
                
                # Simple check: if current quality ID is less than cutoff quality ID
                # This assumes quality IDs are ordered correctly (lower ID = lower quality)
                # A more robust check might involve comparing quality *names* or *scores* if IDs aren't reliable order indicators.
                if current_quality_id is not None and cutoff_quality_id is not None and current_quality_id < cutoff_quality_id:
                    # TODO: Add check for cutoffFormatScore if necessary
                    unmet_movies.append(movie)
            # else: # Log why a movie wasn't considered unmet (optional)
            #     if not has_file: radarr_logger.debug(f"Skipping {movie.get('title')} - no file.")
            #     elif not movie_file: radarr_logger.debug(f"Skipping {movie.get('title')} - no movieFile info.")
            #     elif profile_id not in profile_cutoff_map: radarr_logger.debug(f"Skipping {movie.get('title')} - profile ID {profile_id} not found.")

    radarr_logger.debug(f"Found {len(unmet_movies)} cutoff unmet movies (monitored_only={monitored_only}).")
    return unmet_movies

def refresh_movie(api_url: str, api_key: str, api_timeout: int, movie_id: int) -> Optional[int]:
    """
    Refresh a movie in Radarr.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        movie_id: The ID of the movie to refresh
        
    Returns:
        The command ID if the refresh was triggered successfully, None otherwise
    """
    endpoint = "command"
    data = {
        "name": "RefreshMovie",
        "movieIds": [movie_id]
    }
    
    # Use the updated arr_request
    response = arr_request(api_url, api_key, api_timeout, endpoint, method="POST", data=data)
    if response and 'id' in response:
        command_id = response['id']
        radarr_logger.debug(f"Triggered refresh for movie ID {movie_id}. Command ID: {command_id}")
        return command_id
    else:
        radarr_logger.error(f"Failed to trigger refresh command for movie ID {movie_id}. Response: {response}")
        return None

def movie_search(api_url: str, api_key: str, api_timeout: int, movie_ids: List[int]) -> Optional[int]:
    """
    Trigger a search for one or more movies.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        movie_ids: A list of movie IDs to search for
        
    Returns:
        The command ID if the search command was triggered successfully, None otherwise
    """
    if not movie_ids:
        radarr_logger.warning("No movie IDs provided for search.")
        return None
        
    endpoint = "command"
    data = {
        "name": "MoviesSearch",
        "movieIds": movie_ids
    }
    
    # Use the updated arr_request
    response = arr_request(api_url, api_key, api_timeout, endpoint, method="POST", data=data)
    if response and 'id' in response:
        command_id = response['id']
        radarr_logger.debug(f"Triggered search for movie IDs: {movie_ids}. Command ID: {command_id}")
        return command_id
    else:
        radarr_logger.error(f"Failed to trigger search command for movie IDs {movie_ids}. Response: {response}")
        return None

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """Check the connection to Radarr API."""
    try:
        # Ensure api_url is properly formatted
        if not api_url:
            radarr_logger.error("API URL is empty or not set")
            return False
            
        # Make sure api_url has a scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            radarr_logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
            return False
            
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = api_url.rstrip('/')
        full_url = f"{base_url}/api/v3/system/status"
        
        response = requests.get(full_url, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        radarr_logger.info("Successfully connected to Radarr.")
        return True
    except requests.exceptions.RequestException as e:
        radarr_logger.error(f"Error connecting to Radarr: {e}")
        return False
    except Exception as e:
        radarr_logger.error(f"An unexpected error occurred during Radarr connection check: {e}")
        return False