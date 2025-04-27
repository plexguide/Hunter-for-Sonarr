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
# Correct the import path
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
            
            # Check if there's any content before trying to parse JSON
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError as jde:
                    # Log detailed information about the malformed response
                    sonarr_logger.error(f"Error decoding JSON response from {endpoint}: {str(jde)}")
                    sonarr_logger.error(f"Response status code: {response.status_code}")
                    sonarr_logger.error(f"Response content (first 200 chars): {response.content[:200]}")
                    return None
            else:
                sonarr_logger.debug(f"Empty response content from {endpoint}, returning empty dict")
                return {}
                
        except requests.exceptions.RequestException as e:
            # Add detailed error logging
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_details += f", Status Code: {e.response.status_code}"
                if e.response.content:
                    error_details += f", Content: {e.response.content[:200]}"
            
            sonarr_logger.error(f"Error during {method} request to {endpoint}: {error_details}")
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
        # Ensure api_url is properly formatted
        if not api_url:
            sonarr_logger.error("API URL is empty or not set")
            return False
            
        # Make sure api_url has a scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            sonarr_logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
            return False
            
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = api_url.rstrip('/')
        full_url = f"{base_url}/api/v3/system/status"
        
        response = requests.get(full_url, headers={"X-Api-Key": api_key}, timeout=api_timeout)
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
    """Get missing episodes from Sonarr, handling pagination."""
    endpoint = "wanted/missing"
    page = 1
    page_size = 1000 # Adjust page size if needed, but 1000 is usually good
    all_missing_episodes = []
    retries_per_page = 2
    retry_delay = 3
    
    while True:
        retry_count = 0
        success = False
        
        while retry_count <= retries_per_page and not success:
            # Parameters for the request
            params = {
                "page": page,
                "pageSize": page_size,
                "includeSeries": "true"
            }
            url = f"{api_url}/api/v3/{endpoint}"
            sonarr_logger.debug(f"Requesting missing episodes page {page} (attempt {retry_count+1}/{retries_per_page+1})")
            
            try:
                response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
                response.raise_for_status() # Check for HTTP errors (4xx or 5xx)
                
                if not response.content:
                    sonarr_logger.warning(f"Empty response for missing episodes page {page} (attempt {retry_count+1})")
                    if retry_count < retries_per_page:
                        retry_count += 1
                        time.sleep(retry_delay)
                        continue
                    else:
                        sonarr_logger.error(f"Giving up on empty response after {retries_per_page+1} attempts")
                        break  # Exit the retry loop, continuing to next page or ending
                
                try:
                    data = response.json()
                    records = data.get('records', [])
                    total_records_on_page = len(records)
                    sonarr_logger.debug(f"Parsed {total_records_on_page} missing episode records from page {page}")
                    
                    if not records: # No more records found
                        sonarr_logger.debug(f"No more records found on page {page}. Stopping pagination.")
                        success = True  # Mark as successful even though no records (might be legitimate)
                        break  # Exit retry loop, then also exit pagination loop
                    
                    all_missing_episodes.extend(records)
                    
                    # Check if this was the last page
                    if total_records_on_page < page_size:
                        sonarr_logger.debug(f"Received {total_records_on_page} records (less than page size {page_size}). Last page.")
                        success = True
                        break  # Exit retry loop, then also exit pagination loop
                    
                    # We got records and need to continue - mark success for this page
                    success = True
                    break  # Exit retry loop, continue to next page
                    
                except json.JSONDecodeError as e:
                    sonarr_logger.error(f"Failed to decode JSON for missing episodes page {page} (attempt {retry_count+1}): {e}")
                    if retry_count < retries_per_page:
                        retry_count += 1
                        time.sleep(retry_delay)
                        continue
                    else:
                        sonarr_logger.error(f"Giving up after {retries_per_page+1} failed JSON decode attempts")
                        break  # Exit retry loop, moving to next page or ending
    
            except requests.exceptions.RequestException as e:
                sonarr_logger.error(f"Request error for missing episodes page {page} (attempt {retry_count+1}): {e}")
                if retry_count < retries_per_page:
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                else:
                    sonarr_logger.error(f"Giving up on request after {retries_per_page+1} failed attempts")
                    break  # Exit retry loop
            except Exception as e:
                sonarr_logger.error(f"Unexpected error for missing episodes page {page} (attempt {retry_count+1}): {e}")
                if retry_count < retries_per_page:
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                else:
                    sonarr_logger.error(f"Giving up after unexpected error and {retries_per_page+1} attempts")
                    break  # Exit retry loop
        
        # If we didn't succeed after all retries or there are no more records, stop pagination
        if not success or not records:
            break
            
        # Prepare for the next page
        page += 1
    
    sonarr_logger.info(f"Total missing episodes fetched across all pages: {len(all_missing_episodes)}")

    # Apply monitored filter after fetching all pages
    if monitored_only:
        original_count = len(all_missing_episodes)
        filtered_missing = [
            ep for ep in all_missing_episodes 
            if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
        ]
        sonarr_logger.debug(f"Filtered for monitored_only=True: {len(filtered_missing)} monitored episodes (out of {original_count} total)")
        return filtered_missing
    else:
        sonarr_logger.debug(f"Returning {len(all_missing_episodes)} episodes (monitored_only=False)")
        return all_missing_episodes

def get_cutoff_unmet_episodes(api_url: str, api_key: str, api_timeout: int, monitored_only: bool) -> List[Dict[str, Any]]:
    """Get cutoff unmet episodes from Sonarr, handling pagination."""
    endpoint = "wanted/cutoff"
    page = 1
    page_size = 1000 # Sonarr's max page size for this endpoint
    all_cutoff_unmet = []
    retries_per_page = 2
    retry_delay = 3

    sonarr_logger.debug(f"Starting fetch for cutoff unmet episodes (monitored_only={monitored_only}).")

    while True:
        retry_count = 0
        success = False
        records = []
        
        while retry_count <= retries_per_page and not success:
            # Parameters for the request
            params = {
                "page": page,
                "pageSize": page_size,
                "includeSeries": "true", # Include series info for filtering
                "sortKey": "airDateUtc",
                "sortDir": "asc"
            }
            url = f"{api_url}/api/v3/{endpoint}"
            sonarr_logger.debug(f"Requesting cutoff unmet page {page} (attempt {retry_count+1}/{retries_per_page+1})")

            try:
                response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
                sonarr_logger.debug(f"Sonarr API response status code for cutoff unmet page {page}: {response.status_code}")
                response.raise_for_status() # Check for HTTP errors
                
                if not response.content:
                    sonarr_logger.warning(f"Empty response for cutoff unmet episodes page {page} (attempt {retry_count+1})")
                    if retry_count < retries_per_page:
                        retry_count += 1
                        time.sleep(retry_delay)
                        continue
                    else:
                        sonarr_logger.error(f"Giving up on empty response after {retries_per_page+1} attempts")
                        break

                try:
                    data = response.json()
                    records = data.get('records', [])
                    total_records_on_page = len(records)
                    total_records_reported = data.get('totalRecords', 0)
                    
                    if page == 1:
                        sonarr_logger.info(f"Sonarr API reports {total_records_reported} total cutoff unmet records.")
                    
                    sonarr_logger.debug(f"Parsed {total_records_on_page} cutoff unmet records from page {page}")
                    
                    if not records: # No more records found
                        sonarr_logger.debug(f"No more cutoff unmet records found on page {page}. Stopping pagination.")
                        success = True
                        break

                    all_cutoff_unmet.extend(records)
                    
                    # Check if this was the last page
                    if total_records_on_page < page_size:
                        sonarr_logger.debug(f"Received {total_records_on_page} records (less than page size {page_size}). Last page.")
                        success = True
                        break
                    
                    # Success for this page
                    success = True
                    break
                    
                except json.JSONDecodeError as e:
                    sonarr_logger.error(f"Failed to decode JSON for cutoff unmet page {page} (attempt {retry_count+1}): {e}")
                    if retry_count < retries_per_page:
                        retry_count += 1
                        time.sleep(retry_delay)
                        continue
                    else:
                        sonarr_logger.error(f"Giving up after {retries_per_page+1} failed JSON decode attempts")
                        break
                        
            except requests.exceptions.Timeout as e:
                sonarr_logger.error(f"Timeout for cutoff unmet page {page} (attempt {retry_count+1}): {e}")
                if retry_count < retries_per_page:
                    retry_count += 1
                    # Use a slightly longer retry delay for timeouts
                    time.sleep(retry_delay * 2)
                    continue
                else:
                    sonarr_logger.error(f"Giving up after {retries_per_page+1} timeout failures")
                    break
                    
            except requests.exceptions.RequestException as e:
                error_details = f"Error: {e}"
                if hasattr(e, 'response') and e.response is not None:
                    error_details += f", Status Code: {e.response.status_code}"
                    if hasattr(e.response, 'text') and e.response.text:
                        error_details += f", Response: {e.response.text[:500]}"
                        
                sonarr_logger.error(f"Request error for cutoff unmet page {page} (attempt {retry_count+1}): {error_details}")
                if retry_count < retries_per_page:
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                else:
                    sonarr_logger.error(f"Giving up on request after {retries_per_page+1} failed attempts")
                    break
                    
            except Exception as e:
                sonarr_logger.error(f"Unexpected error for cutoff unmet page {page} (attempt {retry_count+1}): {e}", exc_info=True)
                if retry_count < retries_per_page:
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                else:
                    sonarr_logger.error(f"Giving up after unexpected error and {retries_per_page+1} attempts")
                    break

        # If we didn't succeed after all retries or there are no more records, stop pagination
        if not success or not records:
            break
            
        # Prepare for the next page
        page += 1

    sonarr_logger.info(f"Total cutoff unmet episodes fetched across all pages: {len(all_cutoff_unmet)}")

    # Apply monitored filter after fetching all pages
    if monitored_only:
        original_count = len(all_cutoff_unmet)
        # Ensure series and episode are monitored
        filtered_cutoff_unmet = [
            ep for ep in all_cutoff_unmet
            if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
        ]
        sonarr_logger.debug(f"Filtered for monitored_only=True: {len(filtered_cutoff_unmet)} monitored cutoff unmet episodes remain (out of {original_count} total).")
        return filtered_cutoff_unmet
    else:
        sonarr_logger.debug(f"Returning {len(all_cutoff_unmet)} cutoff unmet episodes (monitored_only=False).")
        return all_cutoff_unmet

def get_cutoff_unmet_episodes_random_page(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, count: int) -> List[Dict[str, Any]]:
    """
    Get a specified number of random cutoff unmet episodes by selecting a random page.
    This is much more efficient for very large libraries.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: Whether to include only monitored episodes
        count: How many episodes to return
        
    Returns:
        A list of randomly selected cutoff unmet episodes
    """
    endpoint = "wanted/cutoff"
    page_size = 100  # Smaller page size to make the initial query faster
    
    # First, make a request to get just the total record count (page 1 with size=1)
    params = {
        "page": 1,
        "pageSize": 1,
        "includeSeries": "true"  # Include series info for filtering
    }
    url = f"{api_url}/api/v3/{endpoint}"
    
    try:
        # Get total record count from a minimal query
        response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
        response.raise_for_status()
        data = response.json()
        total_records = data.get('totalRecords', 0)
        
        if total_records == 0:
            sonarr_logger.info("No cutoff unmet episodes found in Sonarr.")
            return []
            
        # Calculate total pages with our desired page size
        total_pages = (total_records + page_size - 1) // page_size
        sonarr_logger.info(f"Found {total_records} total cutoff unmet episodes across {total_pages} pages")
        
        if total_pages == 0:
            return []
            
        # Select a random page
        import random
        random_page = random.randint(1, total_pages)
        sonarr_logger.info(f"Selected random page {random_page} of {total_pages} for quality upgrade selection")
        
        # Get episodes from the random page
        params = {
            "page": random_page,
            "pageSize": page_size,
            "includeSeries": "true"
        }
        
        response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        sonarr_logger.info(f"Retrieved {len(records)} episodes from page {random_page}")
        
        # Apply monitored filter if requested
        if monitored_only:
            filtered_records = [
                ep for ep in records
                if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
            ]
            sonarr_logger.debug(f"Filtered to {len(filtered_records)} monitored episodes")
            records = filtered_records
        
        # Select random episodes from this page
        if len(records) > count:
            selected_records = random.sample(records, count)
            sonarr_logger.debug(f"Randomly selected {len(selected_records)} episodes from page {random_page}")
            return selected_records
        else:
            # If we have fewer episodes than requested, return all of them
            sonarr_logger.debug(f"Returning all {len(records)} episodes from page {random_page} (fewer than requested {count})")
            return records
            
    except requests.exceptions.RequestException as e:
        sonarr_logger.error(f"Error getting random cutoff unmet episodes from Sonarr: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        sonarr_logger.error(f"Failed to decode JSON response for random cutoff selection: {str(e)}")
        return []
    except Exception as e:
        sonarr_logger.error(f"Unexpected error in random cutoff selection: {str(e)}", exc_info=True)
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
    retries = 2  # Number of retry attempts
    retry_delay = 3  # Delay between retries in seconds
    
    for attempt in range(retries + 1):
        try:
            endpoint = f"{api_url}/api/v3/queue?page=1&pageSize=1" # Just get total count, don't need records
            response = requests.get(endpoint, headers={"X-Api-Key": api_key}, params={"includeSeries": "false"}, timeout=api_timeout)
            response.raise_for_status()
            
            if not response.content:
                sonarr_logger.warning(f"Empty response when getting queue size (attempt {attempt+1}/{retries+1})")
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                return -1
                
            try:
                queue_data = response.json()
                queue_size = queue_data.get('totalRecords', 0)
                sonarr_logger.debug(f"Sonarr download queue size: {queue_size}")
                return queue_size
            except json.JSONDecodeError as jde:
                sonarr_logger.error(f"Failed to decode queue JSON (attempt {attempt+1}/{retries+1}): {jde}")
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                return -1
                
        except requests.exceptions.RequestException as e:
            sonarr_logger.error(f"Error getting Sonarr download queue size (attempt {attempt+1}/{retries+1}): {e}")
            if attempt < retries:
                sonarr_logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            return -1  # Return -1 to indicate an error
        except Exception as e:
            sonarr_logger.error(f"Unexpected error getting queue size (attempt {attempt+1}/{retries+1}): {e}")
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            return -1
            
    # If we get here, all retries failed
    sonarr_logger.error(f"All {retries+1} attempts to get download queue size failed")
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

def get_missing_episodes_random_page(api_url: str, api_key: str, api_timeout: int, monitored_only: bool, count: int) -> List[Dict[str, Any]]:
    """
    Get a specified number of random missing episodes by selecting a random page.
    This is more efficient for very large libraries.
    
    Args:
        api_url: The base URL of the Sonarr API
        api_key: The API key for authentication
        api_timeout: Timeout for the API request
        monitored_only: Whether to include only monitored episodes
        count: How many episodes to return
        
    Returns:
        A list of randomly selected missing episodes
    """
    endpoint = "wanted/missing"
    page_size = 100  # Smaller page size for better performance
    retries = 2
    retry_delay = 3
    
    # First, make a request to get just the total record count (page 1 with size=1)
    params = {
        "page": 1,
        "pageSize": 1,
        "includeSeries": "true"  # Include series info for filtering
    }
    url = f"{api_url}/api/v3/{endpoint}"
    
    for attempt in range(retries + 1):
        try:
            # Get total record count from a minimal query
            sonarr_logger.debug(f"Getting missing episodes count (attempt {attempt+1}/{retries+1})")
            response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
            response.raise_for_status()
            
            if not response.content:
                sonarr_logger.warning(f"Empty response when getting missing count (attempt {attempt+1})")
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                return []
                
            try:
                data = response.json()
                total_records = data.get('totalRecords', 0)
                
                if total_records == 0:
                    sonarr_logger.info("No missing episodes found in Sonarr.")
                    return []
                    
                # Calculate total pages with our desired page size
                total_pages = (total_records + page_size - 1) // page_size
                sonarr_logger.info(f"Found {total_records} total missing episodes across {total_pages} pages")
                
                if total_pages == 0:
                    return []
                    
                # Select a random page
                import random
                random_page = random.randint(1, total_pages)
                sonarr_logger.info(f"Selected random page {random_page} of {total_pages} for missing episodes")
                
                # Get episodes from the random page
                params = {
                    "page": random_page,
                    "pageSize": page_size,
                    "includeSeries": "true"
                }
                
                response = requests.get(url, headers={"X-Api-Key": api_key}, params=params, timeout=api_timeout)
                response.raise_for_status()
                
                if not response.content:
                    sonarr_logger.warning(f"Empty response when getting missing episodes page {random_page}")
                    return []
                    
                try:
                    data = response.json()
                    records = data.get('records', [])
                    sonarr_logger.info(f"Retrieved {len(records)} missing episodes from page {random_page}")
                    
                    # Apply monitored filter if requested
                    if monitored_only:
                        filtered_records = [
                            ep for ep in records
                            if ep.get('series', {}).get('monitored', False) and ep.get('monitored', False)
                        ]
                        sonarr_logger.debug(f"Filtered to {len(filtered_records)} monitored missing episodes")
                        records = filtered_records
                    
                    # Select random episodes from this page
                    if len(records) > count:
                        selected_records = random.sample(records, count)
                        sonarr_logger.debug(f"Randomly selected {len(selected_records)} missing episodes from page {random_page}")
                        return selected_records
                    else:
                        # If we have fewer episodes than requested, return all of them
                        sonarr_logger.debug(f"Returning all {len(records)} missing episodes from page {random_page} (fewer than requested {count})")
                        return records
                        
                except json.JSONDecodeError as jde:
                    sonarr_logger.error(f"Failed to decode JSON response for missing episodes page {random_page}: {str(jde)}")
                    if attempt < retries:
                        time.sleep(retry_delay)
                        continue
                    return []
                    
            except json.JSONDecodeError as jde:
                sonarr_logger.error(f"Failed to decode JSON response for missing episodes count: {str(jde)}")
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                return []
                
        except requests.exceptions.RequestException as e:
            sonarr_logger.error(f"Error getting missing episodes from Sonarr (attempt {attempt+1}): {str(e)}")
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            return []
            
        except Exception as e:
            sonarr_logger.error(f"Unexpected error getting missing episodes (attempt {attempt+1}): {str(e)}", exc_info=True)
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            return []
    
    # If we get here, all retries failed
    sonarr_logger.error("All attempts to get missing episodes failed")
    return []