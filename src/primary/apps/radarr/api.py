#!/usr/bin/env python3
"""
Radarr-specific API functions
Handles all communication with the Radarr API
"""

import requests
import json
import sys
import time
import traceback
from typing import List, Dict, Any, Optional, Union
# Correct the import path
from src.primary.utils.logger import get_logger
from src.primary.settings_manager import get_ssl_verify_setting

# Get logger for the Radarr app
radarr_logger = get_logger("radarr")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Any:
    """
    Make a request to the Radarr API.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call (without /api/v3/)
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data payload for POST/PUT requests
        params: Optional query parameters for GET requests
    
    Returns:
        The parsed JSON response or None if the request failed
    """
    try:
        if not api_url or not api_key:
            radarr_logger.error("No URL or API key provided")
            return None
        
        # Check API limit before making request
        from src.primary.stats_manager import check_hourly_cap_exceeded, increment_hourly_cap
        if check_hourly_cap_exceeded("radarr"):
            radarr_logger.warning("\U0001F6D1 Radarr API hourly limit reached - skipping request")
            return None
        
        # Construct the full URL properly
        full_url = f"{api_url.rstrip('/')}/api/v3/{endpoint.lstrip('/')}"
        
        radarr_logger.debug(f"Making {method} request to: {full_url}")
        
        # Set up headers with the API key
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "Huntarr/1.0 (https://github.com/plexguide/Huntarr.io)"
        }
        
        # Get SSL verification setting
        verify_ssl = get_ssl_verify_setting()
        
        if not verify_ssl:
            radarr_logger.debug("SSL verification disabled by user setting")
        
        # Make the request based on the method
        if method.upper() == "GET":
            response = session.get(full_url, headers=headers, params=params, timeout=api_timeout, verify=verify_ssl)
        elif method.upper() == "POST":
            response = session.post(full_url, headers=headers, json=data, timeout=api_timeout, verify=verify_ssl)
        elif method.upper() == "PUT":
            response = session.put(full_url, headers=headers, json=data, timeout=api_timeout, verify=verify_ssl)
        elif method.upper() == "DELETE":
            response = session.delete(full_url, headers=headers, timeout=api_timeout, verify=verify_ssl)
        else:
            radarr_logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for errors
        response.raise_for_status()
        
        # Increment API usage counter only after successful request
        increment_hourly_cap("radarr")
        
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
    Get a list of movies that don't meet their quality profile cutoff using the proper API endpoint.

    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: If True, only return monitored movies.

    Returns:
        A list of movie objects that need quality upgrades, or None if the request failed.
    """
    # Use Radarr's dedicated cutoff endpoint
    radarr_logger.debug(f"Fetching cutoff unmet movies (monitored_only={monitored_only})...")
    
    # Set up pagination parameters - start with reasonable page size
    page = 1
    page_size = 100  # Reasonable batch size for processing
    all_cutoff_movies = []
    
    while True:
        # Use the proper wanted/cutoff endpoint with pagination
        params = {
            'page': page,
            'pageSize': page_size,
            'monitored': monitored_only
        }
        
        # Use arr_request for proper API tracking and limit checking
        response = arr_request(api_url, api_key, api_timeout, "wanted/cutoff", params=params)
        
        if response is None:
            radarr_logger.error("Failed to retrieve cutoff unmet movies from Radarr API.")
            return None if page == 1 else all_cutoff_movies  # Return partial results if we got some data
            
        # Handle paginated response structure
        records = response.get('records', [])
        total_records = response.get('totalRecords', 0)
        
        if not records:
            break  # No more records
            
        all_cutoff_movies.extend(records)
        
        # Log progress for large datasets
        if total_records > page_size:
            radarr_logger.debug(f"Retrieved {len(all_cutoff_movies)}/{total_records} cutoff unmet movies...")
        
        # Check if we've got all records
        if len(all_cutoff_movies) >= total_records:
            break
            
        page += 1
        
        # Safety check to prevent infinite loops
        if page > 1000:  # Reasonable upper limit
            radarr_logger.warning("Reached maximum page limit (1000) while fetching cutoff unmet movies")
            break

    radarr_logger.debug(f"Found {len(all_cutoff_movies)} cutoff unmet movies (monitored_only={monitored_only}).")
    return all_cutoff_movies

def get_cutoff_unmet_movies_random_page(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, count: int = 50) -> Optional[List[Dict]]:
    """
    Get a random sample of cutoff unmet movies from a random page instead of fetching all pages.
    This dramatically reduces API calls while still providing fair movie selection.
    
    Args:
        api_url: Radarr API URL
        api_key: Radarr API key
        api_timeout: Request timeout in seconds
        monitored_only: Only return monitored movies
        count: Maximum number of movies to return (default: 50)
        
    Returns:
        List of movie dictionaries representing cutoff unmet movies, or None if error
    """
    import random
    
    radarr_logger.debug(f"Fetching random sample of cutoff unmet movies (monitored_only={monitored_only}, count={count})...")
    
    # First, get the first page to determine total pages/records
    params = {
        'page': 1,
        'pageSize': count,  # Use requested count as page size
        'monitored': monitored_only
    }
    
    # Use arr_request for proper API tracking and limit checking
    response = arr_request(api_url, api_key, api_timeout, "wanted/cutoff", params=params)
    
    if response is None:
        radarr_logger.error("Failed to retrieve cutoff unmet movies from Radarr API.")
        return None
        
    records = response.get('records', [])
    total_records = response.get('totalRecords', 0)
    page_size = count
    total_pages = max(1, (total_records + page_size - 1) // page_size)  # Calculate total pages
    
    radarr_logger.info(f"📊 Found {total_records} total cutoff unmet movies across {total_pages} pages")
    
    # If we have few enough records that they fit in one page, just return them
    if total_records <= page_size:
        radarr_logger.info(f"🎯 All {len(records)} movies fit in one page, returning them directly")
        return records
    
    # Pick a random page (excluding page 1 since we already have it)
    if total_pages > 1:
        random_page = random.randint(1, total_pages)
        radarr_logger.info(f"🎲 Randomly selected page {random_page} of {total_pages}")
        
        # If we didn't pick page 1, fetch the random page
        if random_page != 1:
            params['page'] = random_page
            response = arr_request(api_url, api_key, api_timeout, "wanted/cutoff", params=params)
            
            if response is None:
                radarr_logger.warning(f"Failed to fetch random page {random_page}, using page 1 data")
                # Fall back to page 1 data we already have
            else:
                records = response.get('records', [])
                radarr_logger.info(f"📄 Retrieved {len(records)} movies from page {random_page}")
    
    # Randomly sample from the page if we have more than requested
    if len(records) > count:
        records = random.sample(records, count)
        radarr_logger.info(f"🎯 Randomly selected {len(records)} movies from the page")
    
    radarr_logger.info(f"✅ Returning {len(records)} cutoff unmet movies from random sampling")
    return records

def refresh_movie(api_url: str, api_key: str, api_timeout: int, movie_id: int, 
                 command_wait_delay: int = 1, command_wait_attempts: int = 600) -> Optional[int]:
    """
    Refresh functionality has been removed as it was a performance bottleneck.
    This function now returns a placeholder success value without making any API calls.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        movie_id: The ID of the movie to refresh
        command_wait_delay: Seconds to wait between command status checks
        command_wait_attempts: Maximum number of status check attempts
        
    Returns:
        A placeholder command ID (123) to simulate success
    """
    radarr_logger.debug(f"Refresh functionality disabled for movie ID: {movie_id}")
    # Return a placeholder command ID (123) to simulate success without actually refreshing
    return 123

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
        radarr_logger.debug("Successfully connected to Radarr.")
        return True
    except requests.exceptions.RequestException as e:
        radarr_logger.error(f"Error connecting to Radarr: {e}")
        return False
    except Exception as e:
        radarr_logger.error(f"An unexpected error occurred during Radarr connection check: {e}")
        return False

def wait_for_command(api_url: str, api_key: str, api_timeout: int, command_id: int, 
                    delay_seconds: int = 1, max_attempts: int = 600) -> bool:
    """
    Wait for a command to complete.
    
    Args:
        api_url: The base URL of the Radarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        command_id: The ID of the command to wait for
        delay_seconds: Seconds to wait between command status checks
        max_attempts: Maximum number of status check attempts
        
    Returns:
        True if the command completed successfully, False if timed out
    """
    attempts = 0
    while attempts < max_attempts:
        response = arr_request(api_url, api_key, api_timeout, f"command/{command_id}")
        if response and 'state' in response:
            state = response['state']
            if state == "completed":
                return True
            elif state == "failed":
                radarr_logger.error(f"Command {command_id} failed")
                return False
        time.sleep(delay_seconds)
        attempts += 1
    radarr_logger.warning(f"Timed out waiting for command {command_id} to complete")
    return False