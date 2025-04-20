#!/usr/bin/env python3
import os
import requests
import logging
import json
import time
from datetime import datetime, timezone

# Get environment variables
API_KEY = os.environ.get('API_KEY', '')
API_URL = os.environ.get('API_URL', 'http://localhost:8989')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 60))
MAX_RETRIES = 3  # Number of retries for API calls
LOG_EPISODE_ERRORS = os.environ.get('LOG_EPISODE_ERRORS', 'true').lower() == 'true'
DEBUG_API_CALLS = os.environ.get('DEBUG_API_CALLS', 'false').lower() == 'true'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('huntarr-sonarr')

def get_headers():
    """Return the headers needed for API requests."""
    return {
        'X-Api-Key': API_KEY,
        'Content-Type': 'application/json'
    }

def make_request(endpoint, method='GET', data=None, params=None, retries=MAX_RETRIES):
    """Make a request to the Sonarr API with retry capability."""
    url = f"{API_URL}/api/v3/{endpoint}"
    headers = get_headers()
    
    if DEBUG_API_CALLS:
        logger.debug(f"API Request: {method} {url}")
        if params:
            logger.debug(f"Params: {json.dumps(params)}")
        if data:
            logger.debug(f"Data: {json.dumps(data)}")
    
    for attempt in range(retries + 1):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=API_TIMEOUT)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=API_TIMEOUT)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=API_TIMEOUT)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            
            if DEBUG_API_CALLS:
                if response.text:
                    logger.debug(f"API Response: Status {response.status_code}")
                    try:
                        # Try to pretty-print JSON response for debugging
                        resp_data = response.json()
                        if isinstance(resp_data, list) and len(resp_data) > 10:
                            # For large lists, just show the count and first few items
                            logger.debug(f"Response contains {len(resp_data)} items. First few: {json.dumps(resp_data[:3])}")
                        elif isinstance(resp_data, dict) and len(resp_data) > 20:
                            # For large objects, just show keys
                            logger.debug(f"Response contains {len(resp_data)} keys: {list(resp_data.keys())}")
                        else:
                            # For smaller responses, show the full content
                            logger.debug(f"Response: {json.dumps(resp_data)[:1000]}" + ("..." if len(json.dumps(resp_data)) > 1000 else ""))
                    except:
                        # Fall back to just showing response text length if JSON parsing fails
                        logger.debug(f"Response text length: {len(response.text)} characters")
                else:
                    logger.debug("API Response: Empty response body")
            
            return response.json() if response.text.strip() else None
        
        except requests.exceptions.RequestException as e:
            if DEBUG_API_CALLS:
                logger.debug(f"API Request failed: {e}")
                
            if attempt < retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"API request failed (attempt {attempt+1}/{retries+1}): {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"API request failed after {retries+1} attempts: {e}")
                return None

def get_series():
    """Get all series from Sonarr."""
    return make_request('series')

def get_series_by_id(series_id):
    """Get a specific series by ID."""
    return make_request(f'series/{series_id}')

def get_episodes_by_series_id(series_id):
    """Get all episodes for a series with more robust error handling."""
    try:
        return make_request('episode', params={'seriesId': series_id})
    except Exception as e:
        if LOG_EPISODE_ERRORS:
            logger.error(f"Exception retrieving episodes for series ID {series_id}: {e}")
        return []

def refresh_series(series_id):
    """Refresh a series."""
    data = {
        'name': 'RefreshSeries',
        'seriesId': series_id
    }
    result = make_request('command', method='POST', data=data)
    if result:
        logger.info(f"Refresh request sent for series ID {series_id}")
    return result

def search_for_episode(episode_id):
    """Search for a specific episode."""
    data = {
        'name': 'EpisodeSearch',
        'episodeIds': [episode_id]
    }
    result = make_request('command', method='POST', data=data)
    if result:
        logger.info(f"Search request sent for episode ID {episode_id}")
    return result

def search_for_series(series_id):
    """Search for all episodes in a series."""
    data = {
        'name': 'SeriesSearch',
        'seriesId': series_id
    }
    result = make_request('command', method='POST', data=data)
    if result:
        logger.info(f"Search request sent for all episodes in series ID {series_id}")
    return result

def get_queue():
    """Get the current download queue."""
    return make_request('queue')

def is_date_in_future(air_date_str):
    """Check if a date is in the future."""
    if not air_date_str:
        return False
    
    try:
        # Convert ISO format string to datetime with timezone info
        air_date = datetime.fromisoformat(air_date_str.replace('Z', '+00:00'))
        
        # Get current time with timezone info for proper comparison
        now = datetime.now(timezone.utc)
        
        return air_date > now
    except ValueError:
        logger.error(f"Invalid date format: {air_date_str}")
        return False

def get_queue_size():
    """Get the current size of the download queue."""
    queue = get_queue()
    if queue:
        return len(queue['records']) if 'records' in queue else 0
    return 0

def check_api_connection():
    """Check if the API is reachable."""
    try:
        response = requests.get(f"{API_URL}/api/v3/system/status", 
                              headers=get_headers(), 
                              timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Connected to Sonarr version {data.get('version', 'unknown')}")
            return True
        else:
            logger.error(f"API connection failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"API connection check failed: {e}")
        return False