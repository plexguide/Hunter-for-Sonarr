#!/usr/bin/env python3
import os
import requests
import logging
import json
import time
from datetime import datetime

# Get environment variables
API_KEY = os.environ.get('API_KEY', '')
API_URL = os.environ.get('API_URL', 'http://localhost:8989')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 60))

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

def make_request(endpoint, method='GET', data=None, params=None):
    """Make a request to the Sonarr API."""
    url = f"{API_URL}/api/v3/{endpoint}"
    headers = get_headers()
    
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
        return response.json() if response.text.strip() else None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def get_series():
    """Get all series from Sonarr."""
    return make_request('series')

def get_series_by_id(series_id):
    """Get a specific series by ID."""
    return make_request(f'series/{series_id}')

def get_episodes_by_series_id(series_id):
    """Get all episodes for a series."""
    return make_request('episode', params={'seriesId': series_id})

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
        air_date = datetime.fromisoformat(air_date_str.replace('Z', '+00:00'))
        return air_date > datetime.now()
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