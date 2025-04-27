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
        
        response = requests.get(full_url, headers={"X-Api-Key": api_key}, timeout=api_timeout)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info("Successfully connected to Readarr.")
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
            
            # Make the request
            response = session.get(url, headers=headers, timeout=timeout)
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

def arr_request(endpoint: str, method: str = "GET", data: Dict = None, app_type: str = "readarr") -> Any:
    """
    Make a request to the Readarr API.
    
    Args:
        endpoint: The API endpoint to call
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data to send with the request
        app_type: The app type (always readarr for this module)
        
    Returns:
        The JSON response from the API, or None if the request failed
    """
    # Correct the import path
    from src.primary import settings_manager # Use settings_manager instead of keys_manager
    # api_url, api_key = keys_manager.get_api_keys(app_type) # Old way
    api_url = settings_manager.get_setting(app_type, "api_url")
    api_key = settings_manager.get_setting(app_type, "api_key")
    # Get user-configured timeout, fall back to default if not set
    api_timeout = settings_manager.get_setting(app_type, "api_timeout", API_TIMEOUT)
    
    if not api_url or not api_key:
        logger.error("API URL or API key is missing. Check your settings.")
        return None
    
    # Determine the API version
    api_base = "api/v1"  # Readarr uses v1
    
    # Full URL
    url = f"{api_url}/{api_base}/{endpoint}"
    
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

def get_cutoff_unmet_books() -> List[Dict]:
    """
    Get a list of books that don't meet their quality profile cutoff.
    
    Returns:
        A list of book objects that need quality upgrades
    """
    # The cutoffUnmet endpoint in Readarr
    params = "cutoffUnmet=true"
    books = arr_request(f"wanted/cutoff?{params}")
    if not books or "records" not in books:
        return []
    
    return books.get("records", [])

def refresh_author(author_id: int) -> bool:
    """
    Refresh an author in Readarr.
    
    Args:
        author_id: The ID of the author to refresh
        
    Returns:
        True if the refresh was successful, False otherwise
    """
    endpoint = f"command"
    data = {
        "name": "RefreshAuthor",
        "authorId": author_id
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Refreshed author ID {author_id}")
        return True
    return False

def book_search(book_ids: List[int]) -> bool:
    """
    Trigger a search for one or more books.
    
    Args:
        book_ids: A list of book IDs to search for
        
    Returns:
        True if the search command was successful, False otherwise
    """
    endpoint = "command"
    data = {
        "name": "BookSearch",
        "bookIds": book_ids
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Triggered search for book IDs: {book_ids}")
        return True
    return False