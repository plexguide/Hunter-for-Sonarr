#!/usr/bin/env python3
"""
Readarr-specific API functions
Handles all communication with the Readarr API
"""

import requests
import json
import time
import datetime
from typing import List, Dict, Any, Optional, Union
# Correct the import path
from src.primary.utils.logger import get_logger
# Import load_settings
from src.primary.settings_manager import load_settings, get_ssl_verify_setting
import importlib

# Get app-specific logger
logger = get_logger("readarr")

# Use a session for better performance
session = requests.Session()

# Default API timeout in seconds - used as fallback only
API_TIMEOUT = 30

def check_connection(api_url: str, api_key: str, api_timeout: int) -> bool:
    """Check the connection to Readarr API."""
    try:
        # Ensure api_url is properly formatted
        if not api_url:
            logger.error("API URL is empty or not set")
            return False
            
        # Make sure api_url has a scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            logger.error(f"Invalid URL format: {api_url} - URL must start with http:// or https://")
            return False
            
        # Ensure URL doesn't end with a slash before adding the endpoint
        base_url = api_url.rstrip('/')
        full_url = f"{base_url}/api/v1/system/status"
        
        # Add User-Agent header to identify Huntarr
        headers = {
            "X-Api-Key": api_key,
            "User-Agent": "Huntarr/1.0 (https://github.com/plexguide/Huntarr.io)"
        }
        logger.debug(f"Using User-Agent: {headers['User-Agent']}")
        
        response = requests.get(full_url, headers=headers, timeout=api_timeout, verify=get_ssl_verify_setting())
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logger.debug("Successfully connected to Readarr.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Readarr: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Readarr connection check: {e}")
        return False

def get_download_queue_size(api_url: str = None, api_key: str = None, timeout: int = 30) -> int:
    """
    Get the current size of the download queue.
    
    Args:
        api_url: Optional API URL (if not provided, will be fetched from settings)
        api_key: Optional API key (if not provided, will be fetched from settings)
        timeout: Timeout in seconds for the request
    
    Returns:
        The number of items in the download queue, or 0 if the request failed
    """
    try:
        # If API URL and key are provided, use them directly
        if api_url and api_key:
            # Clean up API URL
            api_url = api_url.rstrip('/')
            url = f"{api_url}/api/v1/queue"
            
            # Headers
            headers = {
                "X-Api-Key": api_key,
                "Content-Type": "application/json"
            }
            verify_ssl = get_ssl_verify_setting()
            # Make the request
            response = session.get(url, headers=headers, timeout=timeout, verify=verify_ssl)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            if "totalRecords" in data:
                return data["totalRecords"]
            return 0
        else:
            # Use the arr_request function if API URL and key aren't provided
            response = arr_request("queue")
            if response and "totalRecords" in response:
                return response["totalRecords"]
            return 0
    except Exception as e:
        logger.error(f"Error getting download queue size: {e}")
        return 0

def arr_request(endpoint: str, method: str = "GET", data: Dict = None, app_type: str = "readarr",
                api_url: str = None, api_key: str = None, api_timeout: int = None, 
                params: Dict = None, instance_data: Dict = None) -> Any:
    """
    Make a request to the Readarr API.
    
    This function handles making API requests to Readarr, with automatic
    instance detection or manual override of API details.
    
    Args:
        endpoint: The API endpoint to call (relative path)
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data payload for POST/PUT requests
        app_type: Application type (default: readarr)
        api_url: Optional URL override (if not using instances)
        api_key: Optional API key override (if not using instances)
        api_timeout: Optional timeout override
        params: Optional query parameters
        instance_data: Optional specific instance data to use
        
    Returns:
        The parsed JSON response or None if the request failed
    """
    # Initialize logger
    logger = get_logger(app_type)
    
    # Try to get instance data if not provided directly
    if not instance_data and not (api_url and api_key):
        # Import at function level to avoid circular imports
        try:
            module_name = f'src.primary.apps.{app_type}'
            module = importlib.import_module(module_name)
            if hasattr(module, 'get_configured_instances'):
                instances = module.get_configured_instances()
                if instances:
                    # Use the first instance by default
                    instance_data = instances[0]
        except (ImportError, AttributeError) as e:
            logger.error(f"Error importing module for {app_type}: {e}")
    
    # Get the API details - either from instance_data, direct parameters, or by loading settings
    if instance_data:
        # Instance data directly provided or loaded above
        url = instance_data.get('api_url', '')
        key = instance_data.get('api_key', '')
        timeout = api_timeout or 60  # Default timeout
    elif api_url and api_key:
        # Direct parameters provided
        url = api_url
        key = api_key
        timeout = api_timeout or 60  # Default timeout
    else:
        # No valid parameters, try loading from settings
        try:
            from src.primary.settings_manager import load_settings
            settings = load_settings(app_type)
            url = settings.get('api_url', '')
            key = settings.get('api_key', '')
            timeout = api_timeout or settings.get('api_timeout', 60)
        except Exception as e:
            logger.error(f"Error loading {app_type} settings: {e}")
            return None
    
    # Validate the required parameters
    if not url or not key:
        logger.error(f"Missing API URL or key for {app_type}")
        return None
    
    # Normalize the URL
    url = url.rstrip('/')
    
    # Ensure endpoint starts correctly
    endpoint = endpoint.lstrip('/')
    
    # API version path - different for each app
    api_version = "v1"  # Default for Readarr
    
    # Construct the full URL
    full_url = f"{url}/api/{api_version}/{endpoint}"
    
    # Set up headers
    headers = {
        "X-Api-Key": key,
        "Content-Type": "application/json",
        "User-Agent": f"Huntarr/1.0 ({app_type})"
    }
    
    # Get SSL verification setting
    verify_ssl = get_ssl_verify_setting()
    if not verify_ssl:
        logger.debug("SSL verification disabled by user setting")
    
    # Log the request
    logger.debug(f"Making {method} request to {full_url}")
    
    # Make the request with appropriate method
    try:
        if method.upper() == "GET":
            response = requests.get(full_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl)
        elif method.upper() == "POST":
            response = requests.post(full_url, headers=headers, json=data, timeout=timeout, verify=verify_ssl)
        elif method.upper() == "PUT":
            response = requests.put(full_url, headers=headers, json=data, timeout=timeout, verify=verify_ssl)
        elif method.upper() == "DELETE":
            response = requests.delete(full_url, headers=headers, timeout=timeout, verify=verify_ssl)
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

def get_books_with_missing_files() -> List[Dict]:
    """
    Get a list of books with missing files (not downloaded/available).
    
    Returns:
        A list of book objects with missing files
    """
    # First, get all books
    books = arr_request("book")
    if not books:
        return []
    
    # Filter for books with missing files
    missing_books = []
    for book in books:
        # Check if book is monitored and doesn't have a file
        if book.get("monitored", False) and not book.get("bookFile", None):
            missing_books.append(book)
    
    return missing_books

def get_cutoff_unmet_books(api_url: Optional[str] = None, api_key: Optional[str] = None, api_timeout: Optional[int] = None) -> List[Dict]:
    """
    Get a list of books that don't meet their quality profile cutoff.
    Accepts optional API credentials.
    
    Args:
        api_url: Optional API URL
        api_key: Optional API key
        api_timeout: Optional API timeout
        
    Returns:
        A list of book objects that need quality upgrades
    """
    # The cutoffUnmet endpoint in Readarr
    params = "cutoffUnmet=true"
    # Pass credentials to arr_request
    books = arr_request(f"wanted/cutoff?{params}", api_url=api_url, api_key=api_key, api_timeout=api_timeout)
    if not books or "records" not in books:
        return []
    
    return books.get("records", [])

def get_wanted_missing_books(api_url: str, api_key: str, api_timeout: int, monitored_only: bool = True) -> List[Dict]:
    """
    Get wanted/missing books from Readarr, handling pagination.

    Args:
        api_url: The base URL of the Readarr API.
        api_key: The API key for authentication.
        api_timeout: Timeout for the API request.
        monitored_only: If True, only return monitored books (Readarr API default seems to handle this).

    Returns:
        A list of dictionaries, each representing a missing book, or an empty list on error.
    """
    all_missing_books = []
    page = 1
    page_size = 100 # Adjust as needed, check Readarr API limits
    endpoint = "wanted/missing"

    # Ensure api_url is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        logger.error(f"Invalid URL format: {api_url}")
        return []
    base_url = api_url.rstrip('/')
    url = f"{base_url}/api/v1/{endpoint.lstrip('/')}"
    # Add User-Agent header to identify Huntarr
    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "Huntarr/1.0 (https://github.com/plexguide/Huntarr.io)",
        "Content-Type": "application/json"
    }
    logger.debug(f"Using User-Agent: {headers['User-Agent']}")

    while True:
        params = {
            'page': page,
            'pageSize': page_size,
            # Removed sorting parameters due to potential API issues
            # 'sortKey': 'author.sortName',
            # 'sortDirection': 'ascending',
            # 'monitored': monitored_only # Note: Check if Readarr API supports this directly for wanted/missing
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=api_timeout, verify=get_ssl_verify_setting())
            response.raise_for_status()
            data = response.json()

            if not data or 'records' not in data or not data['records']:
                break # No more data or unexpected format

            all_missing_books.extend(data['records'])

            total_records = data.get('totalRecords', 0)
            if len(all_missing_books) >= total_records:
                break # We have fetched all records

            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching missing books (page {page}) from {url}: {e}")
            return [] # Return empty list on error
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON response from {url} (page {page}). Response: {response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching missing books (page {page}): {e}", exc_info=True)
            return []

    logger.info(f"Successfully fetched {len(all_missing_books)} missing books from Readarr.")
    return all_missing_books

def refresh_author(author_id: int, api_url: Optional[str] = None, api_key: Optional[str] = None, api_timeout: Optional[int] = None) -> bool:
    """
    Refresh functionality has been removed as it was a performance bottleneck.
    This function now returns a success value without making any API calls.
    
    Args:
        author_id: The ID of the author to refresh
        api_url: Optional API URL
        api_key: Optional API key
        api_timeout: Optional API timeout
        
    Returns:
        Always returns True to simulate success
    """
    logger.debug(f"Refresh functionality disabled for author ID: {author_id}")
    # Always return success without making any API calls
    return True

def book_search(book_ids: List[int], api_url: Optional[str] = None, api_key: Optional[str] = None, api_timeout: Optional[int] = None) -> bool:
    """
    Trigger a search for one or more books.
    Accepts optional API credentials.
    
    Args:
        book_ids: A list of book IDs to search for
        api_url: Optional API URL
        api_key: Optional API key
        api_timeout: Optional API timeout
        
    Returns:
        True if the search command was successful, False otherwise
    """
    endpoint = "command"
    data = {
        "name": "BookSearch",
        "bookIds": book_ids
    }
    
    # Pass credentials to arr_request
    response = arr_request(endpoint, method="POST", data=data, api_url=api_url, api_key=api_key, api_timeout=api_timeout)
    # Return the response object (contains command ID) instead of just True/False
    # The calling function expects the command object now.
    return response 

def get_author_details(api_url: str, api_key: str, author_id: int, api_timeout: int = 120) -> Optional[Dict]:
    """Fetches details for a specific author from the Readarr API."""
    endpoint = f"{api_url}/api/v1/author/{author_id}"
    headers = {'X-Api-Key': api_key}
    try:
        response = requests.get(endpoint, headers=headers, timeout=api_timeout, verify=get_ssl_verify_setting())
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        author_data = response.json()
        logger.debug(f"Successfully fetched details for author ID {author_id}.")
        return author_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching author details for ID {author_id} from {endpoint}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching author details for ID {author_id}: {e}")
        return None

def search_books(api_url: str, api_key: str, book_ids: List[int], api_timeout: int = 120) -> Optional[Dict]:
    """Triggers a search for specific book IDs in Readarr."""
    endpoint = f"{api_url}/api/v1/command" # This uses the full URL, not arr_request
    headers = {'X-Api-Key': api_key}
    payload = {
        'name': 'BookSearch',
        'bookIds': book_ids
    }
    try:
        # This uses requests.post directly, not arr_request. It's already correct.
        response = requests.post(endpoint, headers=headers, json=payload, timeout=api_timeout, verify=get_ssl_verify_setting())
        response.raise_for_status()
        command_data = response.json()
        command_id = command_data.get('id')
        logger.info(f"Successfully triggered BookSearch command for book IDs: {book_ids}. Command ID: {command_id}")
        return command_data # Return the full command object which includes the ID
    except requests.exceptions.RequestException as e:
        logger.error(f"Error triggering BookSearch command for book IDs {book_ids} via {endpoint}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred triggering BookSearch for book IDs {book_ids}: {e}")
        return None