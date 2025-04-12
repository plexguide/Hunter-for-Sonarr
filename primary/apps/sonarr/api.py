#!/usr/bin/env python3
"""
Sonarr-specific API functions
Handles all communication with the Sonarr API
"""

import requests
import json
import time
import datetime
from typing import List, Dict, Any, Optional, Union
from primary.utils.logger import get_logger
from primary import settings_manager
from primary.auth import get_app_url_and_key

# Get app-specific logger
logger = get_logger("sonarr")

# Use a session for better performance
session = requests.Session()

# Default API timeout in seconds
API_TIMEOUT = 30

def arr_request(endpoint: str, method: str = "GET", data: Dict = None, app_type: str = "sonarr") -> Any:
    """
    Make a request to the Sonarr API.
    
    Args:
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data payload for POST/PUT requests
        app_type: App type (always 'sonarr' for this module)
    
    Returns:
        The parsed JSON response or None if the request failed
    """
    url, api_key = get_app_url_and_key(app_type)
    
    if not url or not api_key:
        logger.error(f"No URL or API key configured for {app_type}")
        return None
    
    # Construct the full URL
    api_url = f"{url.rstrip('/')}/api/v3/{endpoint.lstrip('/')}"
    
    # Set up headers
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = session.get(api_url, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == "POST":
            response = session.post(api_url, headers=headers, json=data, timeout=API_TIMEOUT)
        elif method.upper() == "PUT":
            response = session.put(api_url, headers=headers, json=data, timeout=API_TIMEOUT)
        elif method.upper() == "DELETE":
            response = session.delete(api_url, headers=headers, timeout=API_TIMEOUT)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check for successful response
        response.raise_for_status()
        
        # Parse response if there is content
        if response.content:
            return response.json()
        else:
            return True
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during {method} request to {endpoint}: {str(e)}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON response from {endpoint}")
        return None

def get_system_status() -> Dict:
    """
    Get Sonarr system status.
    
    Returns:
        System status information or empty dict if request failed
    """
    response = arr_request("system/status")
    if response:
        return response
    return {}

def get_series(series_id: Optional[int] = None) -> Union[List, Dict, None]:
    """
    Get series information from Sonarr.
    
    Args:
        series_id: Optional series ID to get a specific series
    
    Returns:
        List of all series, a specific series, or None if request failed
    """
    if series_id:
        endpoint = f"series/{series_id}"
    else:
        endpoint = "series"
    
    return arr_request(endpoint)

def get_episode(episode_id: int) -> Dict:
    """
    Get episode information by ID.
    
    Args:
        episode_id: The episode ID
    
    Returns:
        Episode information or empty dict if request failed
    """
    response = arr_request(f"episode/{episode_id}")
    if response:
        return response
    return {}

def get_queue() -> List:
    """
    Get the current queue from Sonarr.
    
    Returns:
        Queue information or empty list if request failed
    """
    response = arr_request("queue")
    if not response or "records" not in response:
        return []
    
    return response.get("records", [])

def get_calendar(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List:
    """
    Get calendar information for a date range.
    
    Args:
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
    
    response = arr_request(endpoint)
    if response:
        return response
    return []

def command_status(command_id: str) -> Dict:
    """
    Get the status of a command by ID.
    
    Args:
        command_id: The command ID
    
    Returns:
        Command status information or empty dict if request failed
    """
    response = arr_request(f"command/{command_id}")
    if response:
        return response
    return {}