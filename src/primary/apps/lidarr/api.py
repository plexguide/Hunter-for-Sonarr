#!/usr/bin/env python3
"""
Lidarr-specific API functions
Handles all communication with the Lidarr API (v1)
"""

import requests
import json
import sys
import time
import datetime
import traceback
import logging
from typing import List, Dict, Any, Optional, Union
from src.primary.utils.logger import get_logger

# Get logger for the Lidarr app
lidarr_logger = get_logger("lidarr")

# Use a session for better performance
session = requests.Session()

def arr_request(api_url: str, api_key: str, api_timeout: int, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Any:
    """
    Make a request to the Lidarr API.
    
    Args:
        api_url: The base URL of the Lidarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        params: Optional query parameters
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    if not api_url or not api_key:
        lidarr_logger.error("API URL or API key is missing. Check your settings.")
        return None
        
    # Ensure api_url has a scheme
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        lidarr_logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
        return None
        
    # Make sure URL is properly formed
    full_url = f"{api_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        
    # Set up headers
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
        
    lidarr_logger.debug(f"Lidarr API Request: {method} {full_url} Params: {params} Data: {data}")

    try:
        response = session.request(
            method=method.upper(),
            url=full_url,
            headers=headers,
            json=data if method.upper() in ["POST", "PUT"] else None,
            params=params if method.upper() == "GET" else None,
            timeout=api_timeout
        )
            
        lidarr_logger.debug(f"Lidarr API Response Status: {response.status_code}")
        # Log response body only in debug mode and if small enough
        if lidarr_logger.level == logging.DEBUG and len(response.content) < 1000:
             lidarr_logger.debug(f"Lidarr API Response Body: {response.text}")
        elif lidarr_logger.level == logging.DEBUG:
             lidarr_logger.debug(f"Lidarr API Response Body (truncated): {response.text[:500]}...")

        # Check for successful response
        response.raise_for_status()
            
        # Parse response if there is content
        if response.content and response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        elif response.status_code in [200, 201, 202]: # Success codes that might not return JSON
            return True 
        else: # Should have been caught by raise_for_status, but as a fallback
            lidarr_logger.warning(f"Request successful (status {response.status_code}) but no JSON content returned from {endpoint}")
            return True # Indicate success even without content
                
    except requests.exceptions.RequestException as e:
        error_msg = f"Error during {method} request to Lidarr endpoint '{endpoint}': {str(e)}"
        if e.response is not None:
             error_msg += f" | Status: {e.response.status_code} | Response: {e.response.text[:500]}"
        lidarr_logger.error(error_msg)
        return None
    except json.JSONDecodeError:
        lidarr_logger.error(f"Error decoding JSON response from Lidarr endpoint '{endpoint}'. Response: {response.text[:500]}")
        return None
            
    except Exception as e:
        # Catch all exceptions and log them with traceback
        error_msg = f"CRITICAL ERROR in Lidarr arr_request: {str(e)}"
        lidarr_logger.error(error_msg)
        lidarr_logger.error(f"Full traceback: {traceback.format_exc()}")
        print(error_msg, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None

# --- Specific API Functions ---

def get_system_status(api_url: str, api_key: str, api_timeout: int) -> Optional[Dict]:
    """Get Lidarr system status."""
    return arr_request(api_url, api_key, api_timeout, "system/status")

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """Check the connection to Lidarr API."""
    try:
        # Ensure api_url is properly formatted
        if not api_url:
            lidarr_logger.error("API URL is empty or not set")
            return False
            
        # Make sure api_url has a scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            lidarr_logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
            return False
            
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = api_url.rstrip('/')
        full_url = f"{base_url}/api/v1/system/status"
        
        response = requests.get(full_url, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        lidarr_logger.info("Successfully connected to Lidarr.")
        return True
    except requests.exceptions.RequestException as e:
        lidarr_logger.error(f"Error connecting to Lidarr: {e}")
        return False
    except Exception as e:
        lidarr_logger.error(f"An unexpected error occurred during Lidarr connection check: {e}")
        return False

def get_artists(api_url: str, api_key: str, api_timeout: int, artist_id: Optional[int] = None) -> Union[List, Dict, None]:
    """Get artist information from Lidarr."""
    endpoint = f"artist/{artist_id}" if artist_id else "artist"
    return arr_request(api_url, api_key, api_timeout, endpoint)

def get_albums(api_url: str, api_key: str, api_timeout: int, album_id: Optional[int] = None, artist_id: Optional[int] = None) -> Union[List, Dict, None]:
    """Get album information from Lidarr."""
    params = {}
    if artist_id:
        params['artistId'] = artist_id
        
    if album_id:
        endpoint = f"album/{album_id}"
    else:
        endpoint = "album"
        
    return arr_request(api_url, api_key, api_timeout, endpoint, params=params if params else None)

def get_tracks(api_url: str, api_key: str, api_timeout: int, album_id: Optional[int] = None) -> Union[List, None]:
     """Get track information for a specific album."""
     if not album_id:
         lidarr_logger.warning("get_tracks requires an album_id.")
         return None
     params = {'albumId': album_id}
     return arr_request(api_url, api_key, api_timeout, "track", params=params)

def get_queue(api_url: str, api_key: str, api_timeout: int) -> List:
    """Get the current queue from Lidarr (handles pagination)."""
    # Lidarr v1 queue endpoint supports pagination, unlike Sonarr v3's simple list
    all_records = []
    page = 1
    page_size = 1000 # Request large page size

    while True:
        params = {
            "page": page,
            "pageSize": page_size,
            "sortKey": "timeleft", # Example sort key
            "sortDir": "asc"
        }
        response = arr_request(api_url, api_key, api_timeout, "queue", params=params)
        
        if response and isinstance(response, dict) and 'records' in response:
            records = response.get('records', [])
            if not records:
                break # No more records
            all_records.extend(records)
            
            # Check if this was the last page
            total_records = response.get('totalRecords', 0)
            if len(all_records) >= total_records:
                break
            
            page += 1
        else:
            lidarr_logger.error(f"Failed to get queue page {page} or invalid response format.")
            break # Return what we have so far
            
    return all_records

def get_download_queue_size(api_url: str, api_key: str, api_timeout: int) -> int:
    """Get the current size of the Lidarr download queue."""
    params = {"pageSize": 1} # Only need 1 record to get totalRecords
    response = arr_request(api_url, api_key, api_timeout, "queue", params=params)
    
    if response and isinstance(response, dict) and 'totalRecords' in response:
        queue_size = response.get('totalRecords', 0)
        lidarr_logger.debug(f"Lidarr download queue size: {queue_size}")
        return queue_size
    else:
        lidarr_logger.error("Error getting Lidarr download queue size.")
        return -1 # Indicate error

def get_missing_albums(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """Get missing albums from Lidarr, handling pagination."""
    endpoint = "wanted/missing"
    page = 1
    page_size = 1000 
    all_missing_albums = []
    total_records_reported = -1

    lidarr_logger.debug(f"Starting fetch for missing albums (monitored_only={monitored_only}).")

    while True:
        params = {
            "page": page,
            "pageSize": page_size,
            "includeArtist": "true" # Include artist info for filtering
            # Removed sortKey and sortDir
        }
        
        lidarr_logger.debug(f"Requesting missing albums page {page} with params: {params}")
        response = arr_request(api_url, api_key, api_timeout, endpoint, params=params)

        if response and isinstance(response, dict) and 'records' in response:
            records = response.get('records', [])
            total_records_on_page = len(records)

            if page == 1:
                total_records_reported = response.get('totalRecords', 0)
                lidarr_logger.debug(f"Lidarr API reports {total_records_reported} total missing albums.")

            lidarr_logger.debug(f"Parsed {total_records_on_page} missing album records from Lidarr API JSON (page {page}).")

            if not records:
                lidarr_logger.debug(f"No more missing records found on page {page}. Stopping pagination.")
                break

            all_missing_albums.extend(records)

            if total_records_reported >= 0 and len(all_missing_albums) >= total_records_reported:
                lidarr_logger.debug(f"Fetched {len(all_missing_albums)} records, matching or exceeding total reported ({total_records_reported}). Assuming last page.")
                break

            if total_records_on_page < page_size:
                lidarr_logger.debug(f"Received {total_records_on_page} records (less than page size {page_size}). Assuming last page.")
                break
                
            page += 1
            # time.sleep(0.1) # Optional delay

        else:
            lidarr_logger.error(f"Failed to get missing albums page {page} or invalid response format.")
            break # Return what we have so far
            
    lidarr_logger.info(f"Total missing albums fetched across all pages: {len(all_missing_albums)}")

    # Apply monitored filter after fetching
    if monitored_only:
        original_count = len(all_missing_albums)
        # Check both album and artist monitored status
        filtered_missing = [
            album for album in all_missing_albums
            if album.get('monitored', False) and album.get('artist', {}).get('monitored', False)
        ]
        lidarr_logger.debug(f"Filtered for monitored_only=True: {len(filtered_missing)} monitored missing albums remain (out of {original_count} total).")
        return filtered_missing
    else:
        lidarr_logger.debug(f"Returning {len(all_missing_albums)} missing albums (monitored_only=False).")
        return all_missing_albums

def get_cutoff_unmet_albums(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """Get cutoff unmet albums from Lidarr, handling pagination."""
    # Note: Lidarr API returns ALBUMS for cutoff unmet, not tracks.
    endpoint = "wanted/cutoff"
    page = 1
    page_size = 1000 # Adjust page size if needed, Lidarr default might be smaller
    all_cutoff_unmet = []
    total_records_reported = -1

    lidarr_logger.debug(f"Starting fetch for cutoff unmet albums (monitored_only={monitored_only}).")

    while True:
        params = {
            "page": page,
            "pageSize": page_size,
            "includeArtist": "true" # Include artist info for filtering
            # Removed sortKey and sortDir
        }
        
        lidarr_logger.debug(f"Requesting cutoff unmet albums page {page} with params: {params}")
        response = arr_request(api_url, api_key, api_timeout, endpoint, params=params)
        
        if response and isinstance(response, dict) and 'records' in response:
            records = response.get('records', [])
            total_records_on_page = len(records)

            if page == 1:
                total_records_reported = response.get('totalRecords', 0)
                lidarr_logger.debug(f"Lidarr API reports {total_records_reported} total cutoff unmet albums.")

            lidarr_logger.debug(f"Parsed {total_records_on_page} cutoff unmet album records from Lidarr API JSON (page {page}).")

            if not records:
                lidarr_logger.debug(f"No more cutoff unmet records found on page {page}. Stopping pagination.")
                break

            all_cutoff_unmet.extend(records)

            # Check if we have fetched all reported records
            if total_records_reported >= 0 and len(all_cutoff_unmet) >= total_records_reported:
                lidarr_logger.debug(f"Fetched {len(all_cutoff_unmet)} records, matching or exceeding total reported ({total_records_reported}). Assuming last page.")
                break

            # Check if the number of records received is less than the page size
            if total_records_on_page < page_size:
                lidarr_logger.debug(f"Received {total_records_on_page} records (less than page size {page_size}). Assuming last page.")
                break
                
            page += 1
            # time.sleep(0.1) # Optional small delay between pages

        else:
            # Log the error based on the response received (handled in arr_request)
            lidarr_logger.error(f"Error getting cutoff unmet albums from Lidarr (page {page}) or invalid response format. Stopping pagination.")
            # Return what we have so far, or indicate complete failure? Let's return what we have.
            break 

    lidarr_logger.info(f"Total cutoff unmet albums fetched across all pages: {len(all_cutoff_unmet)}")

    # Apply monitored filter after fetching all pages
    if monitored_only:
        original_count = len(all_cutoff_unmet)
        # Check both album and artist monitored status
        filtered_cutoff_unmet = [
            album for album in all_cutoff_unmet
            if album.get('monitored', False) and album.get('artist', {}).get('monitored', False)
        ]
        lidarr_logger.debug(f"Filtered for monitored_only=True: {len(filtered_cutoff_unmet)} monitored cutoff unmet albums remain (out of {original_count} total).")
        return filtered_cutoff_unmet
    else:
        lidarr_logger.debug(f"Returning {len(all_cutoff_unmet)} cutoff unmet albums (monitored_only=False).")
        return all_cutoff_unmet

def search_albums(api_url: str, api_key: str, api_timeout: int, album_ids: List[int]) -> Optional[Dict]:
    """Trigger a search for specific albums in Lidarr."""
    if not album_ids:
        lidarr_logger.warning("No album IDs provided for search.")
        return None
        
    payload = {
        "name": "AlbumSearch",
        "albumIds": album_ids
    }
    response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload)
    
    if response and isinstance(response, dict) and 'id' in response:
        command_id = response.get('id')
        lidarr_logger.info(f"Triggered Lidarr AlbumSearch for album IDs: {album_ids}. Command ID: {command_id}")
        return response # Return the full command object including ID
    else:
        lidarr_logger.error(f"Failed to trigger Lidarr AlbumSearch for album IDs {album_ids}. Response: {response}")
        return None

def search_artist(api_url: str, api_key: str, api_timeout: int, artist_id: int) -> Optional[Dict]:
    """Trigger a search for a specific artist in Lidarr."""
    payload = {
        "name": "ArtistSearch",
        "artistIds": [artist_id]
    }
    response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload)

    if response and isinstance(response, dict) and 'id' in response:
        command_id = response.get('id')
        lidarr_logger.info(f"Triggered Lidarr ArtistSearch for artist ID: {artist_id}. Command ID: {command_id}")
        return response # Return the full command object
    else:
        lidarr_logger.error(f"Failed to trigger Lidarr ArtistSearch for artist ID {artist_id}. Response: {response}")
        return None

def refresh_artist(api_url: str, api_key: str, api_timeout: int, artist_id: int) -> Optional[Dict]:
    """Trigger a refresh for a specific artist in Lidarr."""
    payload = {
        "name": "RefreshArtist",
        "artistId": artist_id
    }
    response = arr_request(api_url, api_key, api_timeout, "command", method="POST", data=payload)

    if response and isinstance(response, dict) and 'id' in response:
        command_id = response.get('id')
        lidarr_logger.info(f"Triggered Lidarr RefreshArtist for artist ID: {artist_id}. Command ID: {command_id}")
        return response # Return the full command object
    else:
        lidarr_logger.error(f"Failed to trigger Lidarr RefreshArtist for artist ID {artist_id}. Response: {response}")
        return None

def get_command_status(api_url: str, api_key: str, api_timeout: int, command_id: int) -> Optional[Dict[str, Any]]:
    """Get the status of a Lidarr command."""
    response = arr_request(api_url, api_key, api_timeout, f"command/{command_id}")
    if response and isinstance(response, dict):
        lidarr_logger.debug(f"Checked Lidarr command status for ID {command_id}: {response.get('status')}")
        return response
    else:
         lidarr_logger.error(f"Error getting Lidarr command status for ID {command_id}. Response: {response}")
         return None

def get_artist_by_id(api_url: str, api_key: str, api_timeout: int, artist_id: int) -> Optional[Dict[str, Any]]:
    """Get artist details by ID from Lidarr."""
    return arr_request(api_url, api_key, api_timeout, f"artist/{artist_id}")