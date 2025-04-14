#!/usr/bin/env python3
"""
Sonarr API Helper Functions
Handles all communication with the Sonarr API
"""

import requests
import time
from typing import List, Dict, Any, Optional, Union
from primary.utils.logger import logger, debug_log
from primary.config import API_KEY, API_URL, API_TIMEOUT, COMMAND_WAIT_DELAY, COMMAND_WAIT_ATTEMPTS

# Create a session for reuse
session = requests.Session()

def arr_request(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Union[Dict, List]]:
    """
    Make a request to the Sonarr API.
    `endpoint` should be something like 'series', 'command', 'wanted/cutoff', etc.
    """
    # Sonarr uses API v3
    api_base = "api/v3"
    
    url = f"{API_URL}/{api_base}/{endpoint}"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = session.get(url, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == "POST":
            response = session.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for 401 Unauthorized or other error status codes
        if response.status_code == 401:
            logger.error(f"API request error: 401 Client Error: Unauthorized for url: {url}")
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return None

def check_connection(app_type: str = None) -> bool:
    """
    Check if we can connect to the Sonarr API.
    Returns True if connection is successful, False otherwise.
    
    Args:
        app_type: Optional parameter kept for compatibility, ignored as we only support Sonarr
    """
    # Get API credentials
    from primary import keys_manager
    api_url, api_key = keys_manager.get_api_keys("sonarr")
    
    # First explicitly check if API URL and Key are configured
    if not api_url:
        logger.error("Sonarr API URL is not configured in settings. Please set it up in the Settings page.")
        return False
    
    if not api_key:
        logger.error("Sonarr API Key is not configured in settings. Please set it up in the Settings page.")
        return False
    
    # Log what we're attempting to connect to
    logger.debug(f"Attempting to connect to Sonarr at {api_url}")
    
    # Try to access the system/status endpoint
    try:
        endpoint = "system/status"
        api_base = "api/v3"  # Sonarr uses v3
        
        url = f"{api_url}/{api_base}/{endpoint}"
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Testing connection with URL: {url}")
        response = session.get(url, headers=headers, timeout=API_TIMEOUT)
        
        if response.status_code == 401:
            logger.error("Connection test failed: 401 Client Error: Unauthorized - Invalid API key for Sonarr")
            return False
            
        response.raise_for_status()
        logger.info(f"Connection to Sonarr at {api_url} successful")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test failed for Sonarr: {e}")
        return False

def wait_for_command(command_id: int):
    """Wait for a Sonarr command to complete."""
    logger.debug(f"Waiting for command {command_id} to complete...")
    attempts = 0
    while True:
        try:
            time.sleep(COMMAND_WAIT_DELAY)
            response = arr_request(f"command/{command_id}")
            logger.debug(f"Command {command_id} Status: {response['status']}")
        except Exception as error:
            logger.error(f"Error fetching command status on attempt {attempts + 1}: {error}")
            return False

        attempts += 1

        if response['status'].lower() in ['complete', 'completed'] or attempts >= COMMAND_WAIT_ATTEMPTS:
            break

    if response['status'].lower() not in ['complete', 'completed']:
        logger.warning(f"Command {command_id} did not complete within the allowed attempts.")
        return False

    time.sleep(0.5)

    return response['status'].lower() in ['complete', 'completed']

# Sonarr-specific functions
def get_series() -> List[Dict]:
    """Get all series from Sonarr."""
    series_list = arr_request("series")
    if series_list:
        debug_log("Raw series API response sample:", series_list[:2] if len(series_list) > 2 else series_list)
    return series_list or []

def refresh_series(series_id: int) -> bool:
    """
    Refresh a specific series in Sonarr.
    
    POST /api/v3/command
    {
      "name": "RefreshSeries",
      "seriesId": <series_id>
    }
    """
    data = {
        "name": "RefreshSeries",
        "seriesId": series_id
    }
    response = arr_request("command", method="POST", data=data)
    if not response or 'id' not in response:
        return False
    return wait_for_command(response['id'])

def episode_search_episodes(episode_ids: List[int]) -> bool:
    """
    Search for episodes in Sonarr.
    
    POST /api/v3/command
    {
      "name": "EpisodeSearch",
      "episodeIds": [...]
    }
    """
    data = {
        "name": "EpisodeSearch",
        "episodeIds": episode_ids
    }
    response = arr_request("command", method="POST", data=data)
    if not response or 'id' not in response:
        return False
    return wait_for_command(response['id'])

def get_download_queue_size() -> int:
    """
    Get the number of items currently downloading.
    
    GET /api/v3/queue?status=downloading
    Returns total number of items in the queue with the status 'downloading'.
    """
    response = arr_request("queue?status=downloading")
    if not response:
        return 0
        
    total_records = response.get("totalRecords", 0)
    if not isinstance(total_records, int):
        total_records = 0
    logger.debug(f"Download Queue Size: {total_records}")

    return total_records

def get_cutoff_unmet(page: int = 1) -> Optional[Dict]:
    """
    Get episodes that don't meet their quality cutoff.
    
    GET /api/v3/wanted/cutoff?sortKey=airDateUtc&sortDirection=descending&includeSeriesInformation=true
        &page=<page>&pageSize=200
    Returns JSON with a "records" array and "totalRecords".
    """
    endpoint = (
        "wanted/cutoff?"
        "sortKey=airDateUtc&sortDirection=descending&includeSeriesInformation=true"
        f"&page={page}&pageSize=200"
    )
    return arr_request(endpoint, method="GET")

def get_cutoff_unmet_total_pages() -> int:
    """
    Find the total number of pages of episodes that don't meet their quality cutoff.
    """
    response = arr_request("wanted/cutoff?page=1&pageSize=1")
    if not response or "totalRecords" not in response:
        return 0
    
    total_records = response.get("totalRecords", 0)
    if not isinstance(total_records, int) or total_records < 1:
        return 0
    
    # Each page has up to 200 episodes
    total_pages = (total_records + 200 - 1) // 200
    return max(total_pages, 1)

def get_episodes_for_series(series_id: int) -> Optional[List[Dict]]:
    """Get all episodes for a specific series"""
    return arr_request(f"episode?seriesId={series_id}", method="GET")

def get_missing_episodes(pageSize: int = 1000) -> Optional[Dict]:
    """
    Get missing episodes from Sonarr.
    
    GET /api/v3/wanted/missing?pageSize=<pageSize>&includeSeriesInformation=true
    Returns JSON with a "records" array of missing episodes and "totalRecords".
    """
    endpoint = f"wanted/missing?pageSize={pageSize}&includeSeriesInformation=true"
    result = arr_request(endpoint, method="GET")
    
    # Better debugging for missing episodes query
    if result:
        logger.debug(f"Found {result.get('totalRecords', 0)} total missing episodes")
        if result.get('records'):
            logger.debug(f"First few missing episodes: {result['records'][:2] if len(result['records']) > 2 else result['records']}")
    else:
        logger.warning("Missing episodes query returned no data")
    
    return result

def get_series_with_missing_episodes() -> List[Dict]:
    """
    Fetch all shows that have missing episodes using the wanted/missing endpoint.
    Returns a list of series objects with an additional 'missingEpisodes' field 
    containing the list of missing episodes for that series.
    """
    # Log request attempt
    logger.debug("Requesting missing episodes from Sonarr API")
    
    missing_data = get_missing_episodes()
    if not missing_data or "records" not in missing_data:
        logger.error("Failed to get missing episodes data or no 'records' field in response")
        return []
    
    # Group missing episodes by series ID
    series_with_missing = {}
    for episode in missing_data.get("records", []):
        series_id = episode.get("seriesId")
        if not series_id:
            logger.warning(f"Found episode without seriesId: {episode}")
            continue
            
        series_title = None
        
        # Try to get series info from the episode record
        if "series" in episode and isinstance(episode["series"], dict):
            series_info = episode["series"]
            series_title = series_info.get("title")
            
            # Initialize the series entry if it doesn't exist
            if series_id not in series_with_missing:
                series_with_missing[series_id] = {
                    "id": series_id,
                    "title": series_title or "Unknown Show",
                    "monitored": series_info.get("monitored", False),
                    "missingEpisodes": []
                }
        else:
            # If we don't have series info, need to fetch it
            if series_id not in series_with_missing:
                # Get series info directly
                series_info = arr_request(f"series/{series_id}", method="GET")
                if series_info:
                    series_with_missing[series_id] = {
                        "id": series_id,
                        "title": series_info.get("title", "Unknown Show"),
                        "monitored": series_info.get("monitored", False),
                        "missingEpisodes": []
                    }
                else:
                    logger.warning(f"Could not get series info for ID {series_id}, skipping episode")
                    continue
        
        # Add the episode to the series record
        if series_id in series_with_missing:
            series_with_missing[series_id]["missingEpisodes"].append(episode)
    
    # Convert to list and add count for convenience
    result = []
    for series_id, series_data in series_with_missing.items():
        series_data["missingEpisodeCount"] = len(series_data["missingEpisodes"])
        result.append(series_data)
    
    logger.debug(f"Processed missing episodes data into {len(result)} series with missing episodes")
    return result