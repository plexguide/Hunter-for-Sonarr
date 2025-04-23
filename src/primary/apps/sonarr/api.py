#!/usr/bin/env python3
"""
Sonarr-specific API functions
Handles all communication with the Sonarr API
"""

import requests
import json
import sys
import time
import datetime
import traceback
from typing import List, Dict, Any, Optional, Union
from src.primary.utils.logger import get_logger

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """
    Make a request to the Sonarr API.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data payload for POST/PUT requests
    
    Returns:
        The parsed JSON response or None if the request failed
    """
    try:
        if not api_url or not api_key:
            sonarr_logger.error("No URL or API key provided")
            return None
        
        # Construct the full URL
        api_url = f"{api_url.rstrip('/')}/api/v3/{endpoint.lstrip('/')}"
        
        # Set up headers
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = session.get(api_url, headers=headers, timeout=api_timeout)
            elif method.upper() == "POST":
                response = session.post(api_url, headers=headers, json=data, timeout=api_timeout)
            elif method.upper() == "PUT":
                response = session.put(api_url, headers=headers, json=data, timeout=api_timeout)
            elif method.upper() == "DELETE":
                response = session.delete(api_url, headers=headers, timeout=api_timeout)
            else:
                sonarr_logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse response if there is content
            if response.content:
                return response.json()
            else:
                return True
                
        except requests.exceptions.RequestException as e:
            sonarr_logger.error(f"Error during {method} request to {endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError:
            sonarr_logger.error(f"Error decoding JSON response from {endpoint}")
            return None
    except Exception as e:
        # Catch all exceptions and log them with traceback
        error_msg = f"CRITICAL ERROR in arr_request: {str(e)}"
        sonarr_logger.error(error_msg)
        sonarr_logger.error(f"Full traceback: {traceback.format_exc()}")
        print(error_msg, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None

def get_system_status(api_url: str, api_key: str, api_timeout: int) -> Dict:
    """
    Get Sonarr system status.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
    
    Returns:
        System status information or empty dict if request failed
    """
    response = arr_request(api_url, api_key, api_timeout, "system/status")
    if response:
        return response
    return {}

def get_series(api_url: str, api_key: str, api_timeout: int, series_id: Optional[int] = None) -> Union[List, Dict, None]:
    """
    Get series information from Sonarr.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        series_id: Optional series ID to get a specific series
    
    Returns:
        List of all series, a specific series, or None if request failed
    """
    if series_id:
        endpoint = f"series/{series_id}"
    else:
        endpoint = "series"
    
    return arr_request(api_url, api_key, api_timeout, endpoint)

def get_episode(api_url: str, api_key: str, api_timeout: int, episode_id: int) -> Dict:
    """
    Get episode information by ID.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        episode_id: The episode ID
    
    Returns:
        Episode information or empty dict if request failed
    """
    response = arr_request(api_url, api_key, api_timeout, f"episode/{episode_id}")
    if response:
        return response
    return {}

def get_queue(api_url: str, api_key: str, api_timeout: int) -> List:
    """
    Get the current queue from Sonarr.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
    
    Returns:
        Queue information or empty list if request failed
    """
    response = arr_request(api_url, api_key, api_timeout, "queue")
    if not response or "records" not in response:
        return []
    
    return response.get("records", [])

def get_calendar(api_url: str, api_key: str, api_timeout: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List:
    """
    Get calendar information for a date range.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
    
    Returns:
        Calendar information or empty list if request failed
    """
    params = []
    
    if start_date:
        params.append(f"start={start_date}")
    
    if end_date:
        params.append(f"end={end_date}")
    
    endpoint = "calendar"
    if params:
        endpoint = f"{endpoint}?{'&'.join(params)}"
    
    response = arr_request(api_url, api_key, api_timeout, endpoint)
    if response:
        return response
    return []

def command_status(api_url: str, api_key: str, api_timeout: int, command_id: str) -> Dict:
    """
    Get the status of a command by ID.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        command_id: The command ID
    
    Returns:
        Command status information or empty dict if request failed
    """
    response = arr_request(api_url, api_key, api_timeout, f"command/{command_id}")
    if response:
        return response
    return {}

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """Check the connection to Sonarr API."""
    try:
        response = requests.get(f"{api_url}/api/v3/system/status", headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        sonarr_logger.info("Successfully connected to Sonarr.")
        return True
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error connecting to Sonarr: {e}")
        return False
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred during Sonarr connection check: {e}")
        return False

def get_missing_episodes(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """Get missing episodes from Sonarr."""
    try:
        endpoint = f"{api_url}/api/v3/wanted/missing?page=1&pageSize=1000&sortKey=airDateUtc&sortDir=asc"
        response = requests.get(endpoint, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status()
        missing = response.json().get('records', [])
        
        if monitored_only:
            # Filter for monitored series and episodes if monitored_only is True
            filtered_missing = [
                ep for ep in missing 
                if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
            ]
            sonarr_logger.debug(f"Found {len(filtered_missing)} monitored missing episodes (out of {len(missing)} total).")
            return filtered_missing
        else:
            sonarr_logger.debug(f"Found {len(missing)} missing episodes (monitored_only is False).")
            return missing
            
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting missing episodes from Sonarr: {e}")
        return []
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while getting missing episodes: {e}")
        return []

def get_cutoff_unmet_episodes(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """Get cutoff unmet episodes from Sonarr."""
    try:
        endpoint = f"{api_url}/api/v3/wanted/cutoff?page=1&pageSize=1000&sortKey=airDateUtc&sortDir=asc"
        response = requests.get(endpoint, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status()
        cutoff_unmet = response.json().get('records', [])
        
        if monitored_only:
            # Filter for monitored series and episodes if monitored_only is True
            filtered_cutoff_unmet = [
                ep for ep in cutoff_unmet 
                if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
            ]
            sonarr_logger.debug(f"Found {len(filtered_cutoff_unmet)} monitored cutoff unmet episodes (out of {len(cutoff_unmet)} total).")
            return filtered_cutoff_unmet
        else:
            sonarr_logger.debug(f"Found {len(cutoff_unmet)} cutoff unmet episodes (monitored_only is False).")
            return cutoff_unmet
            
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting cutoff unmet episodes from Sonarr: {e}")
        return []
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while getting cutoff unmet episodes: {e}")
        return []

def search_episode(api_url: str, api_key: str, api_timeout: int, episode_ids: List[int]) -> Optional[int]:
    """Trigger a search for specific episodes in Sonarr."""
    if not episode_ids:
        sonarr_logger.warning("No episode IDs provided for search.")
        return None
    try:
        endpoint = f"{api_url}/api/v3/command"
        payload = {
            "name": "EpisodeSearch",
            "episodeIds": episode_ids
        }
        response = requests.post(endpoint, headers={"X-Api-Key": api_key}, json=payload, timeout=api_timeout)
        response.raise_for_status()
        command_id = response.json().get('id')
        sonarr_logger.info(f"Triggered Sonarr search for episode IDs: {episode_ids}. Command ID: {command_id}")
        return command_id
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error triggering Sonarr search for episode IDs {episode_ids}: {e}")
        return None
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while triggering Sonarr search: {e}")
        return None

def get_command_status(api_url: str, api_key: str, api_timeout: int, command_id: int) -> Optional[Dict[str, Any]]:
    """Get the status of a Sonarr command."""
    try:
        endpoint = f"{api_url}/api/v3/command/{command_id}"
        response = requests.get(endpoint, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status()
        status = response.json()
        sonarr_logger.debug(f"Checked Sonarr command status for ID {command_id}: {status.get('status')}")
        return status
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting Sonarr command status for ID {command_id}: {e}")
        return None
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while getting Sonarr command status: {e}")
        return None

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int) -> int:
    """Get the current size of the Sonarr download queue."""
    try:
        endpoint = f"{api_url}/api/v3/queue?page=1&pageSize=1000" # Fetch a large page size
        response = requests.get(endpoint, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status()
        queue_data = response.json()
        queue_size = queue_data.get('totalRecords', 0)
        sonarr_logger.debug(f"Sonarr download queue size: {queue_size}")
        return queue_size
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting Sonarr download queue size: {e}")
        return -1 # Return -1 to indicate an error
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while getting Sonarr queue size: {e}")
        return -1

def refresh_series(api_url: str, api_key: str, api_timeout: int, series_id: int) -> Optional[int]:
    """Trigger a refresh for a specific series in Sonarr."""
    try:
        endpoint = f"{api_url}/api/v3/command"
        payload = {
            "name": "RefreshSeries",
            "seriesId": series_id
        }
        response = requests.post(endpoint, headers={"X-Api-Key": api_key}, json=payload, timeout=api_timeout)
        response.raise_for_status()
        command_id = response.json().get('id')
        sonarr_logger.info(f"Triggered Sonarr refresh for series ID: {series_id}. Command ID: {command_id}")
        return command_id
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error triggering Sonarr refresh for series ID {series_id}: {e}")
        return None
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while triggering Sonarr series refresh: {e}")
        return None

def get_series_by_id(api_url: str, api_key: str, api_timeout: int, series_id: int) -> Optional[Dict[str, Any]]:
    """Get series details by ID from Sonarr."""
    try:
        endpoint = f"{api_url}/api/v3/series/{series_id}"
        response = requests.get(endpoint, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status()
        series_data = response.json()
        sonarr_logger.debug(f"Fetched details for Sonarr series ID: {series_id}")
        return series_data
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting Sonarr series details for ID {series_id}: {e}")
        return None
    except Exception as e:
        sonarr_logger.error(f"An unexpected error occurred while getting Sonarr series details: {e}")
        return None