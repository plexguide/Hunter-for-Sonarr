#!/usr/bin/env python3
"""
Missing Books Processing for Readarr
Handles searching for missing books in Readarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.readarr import api as readarr_api
from src.primary.stats_manager import increment_stat
from src.primary.stateful_manager import is_processed, add_processed_id
from src.primary.utils.history_utils import log_processed_media
from src.primary.state import check_state_reset

# Get logger for the app
readarr_logger = get_logger("readarr")

def process_missing_books(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing books in Readarr based on provided settings.
    
    Args:
        app_settings: Dictionary containing all settings for Readarr
        stop_check: A function that returns True if the process should stop
    
    Returns:
        True if any books were processed, False otherwise.
    """
    readarr_logger.info("Starting missing books processing cycle for Readarr.")
    processed_any = False
    
    # Reset state files if enough time has passed
    check_state_reset("readarr")
    
    # Get the settings for the instance
    general_settings = readarr_api.load_settings('general')
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    instance_name = app_settings.get("instance_name", "Readarr Default")
    
    # Use the centralized timeout from general settings with app-specific as fallback
    api_timeout = general_settings.get("api_timeout", app_settings.get("api_timeout", 90))  # Use centralized timeout
    readarr_logger.info(f"Using API timeout of {api_timeout} seconds for Readarr")
    
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_author_refresh = app_settings.get("skip_author_refresh", False)
    hunt_missing_books = app_settings.get("hunt_missing_books", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)

    # Get missing books
    readarr_logger.info("Retrieving wanted/missing books...")
    readarr_logger.info("Retrieving wanted/missing books...")

    # Call the correct function to get missing books
    missing_books_data = readarr_api.get_wanted_missing_books(api_url, api_key, api_timeout, monitored_only)

    if missing_books_data is None: # Check if None was returned due to an API error
        readarr_logger.error(f"Failed to retrieve missing books data. Skipping processing.")
        return False
        
    readarr_logger.info(f"Found {len(missing_books_data)} missing books.")

    # Group by author ID (optional)
    books_by_author = {}
    for book in missing_books_data:
        author_id = book.get("authorId")
        if author_id:
            if author_id not in books_by_author:
                books_by_author[author_id] = []
            books_by_author[author_id].append(book)

    author_ids = list(books_by_author.keys())

    # Filter out already processed authors using stateful management
    unprocessed_authors = []
    for author_id in author_ids:
        if not is_processed("readarr", instance_name, str(author_id)):
            unprocessed_authors.append(author_id)
        else:
            readarr_logger.debug(f"Skipping already processed author ID: {author_id}")

    readarr_logger.info(f"Found {len(unprocessed_authors)} unprocessed authors out of {len(author_ids)} total authors with missing books.")
    
    if not unprocessed_authors:
        readarr_logger.info(f"No unprocessed authors found for {instance_name}. All available authors have been processed.")
        return False

    # Always randomly select authors/books to process
    readarr_logger.info(f"Randomly selecting up to {hunt_missing_books} authors with missing books.")
    authors_to_process = random.sample(unprocessed_authors, min(hunt_missing_books, len(unprocessed_authors)))

    readarr_logger.info(f"Selected {len(authors_to_process)} authors to search for missing books.")
    processed_count = 0
    processed_something = False
    processed_authors = [] # Track author names processed

    for author_id in authors_to_process:
        if stop_check():
            readarr_logger.info("Stop signal received, aborting Readarr missing cycle.")
            break

        author_info = readarr_api.get_author_details(api_url, api_key, author_id, api_timeout) # Assuming this exists
        author_name = author_info.get("authorName", f"Author ID {author_id}") if author_info else f"Author ID {author_id}"

        readarr_logger.info(f"Processing missing books for author: \"{author_name}\" (Author ID: {author_id})")

        # Refresh author (optional)
        if not skip_author_refresh:
            readarr_logger.info(f"  - Refreshing author info...")
            refresh_result = readarr_api.refresh_author(api_url, api_key, author_id, api_timeout) # Assuming this exists
            time.sleep(5) # Basic wait
            if not refresh_result:
                 readarr_logger.warning(f"  - Failed to trigger author refresh. Continuing search anyway.")
        else:
            readarr_logger.info(f"  - Skipping author refresh (skip_author_refresh=true)")

        # Search for missing books associated with the author
        readarr_logger.info(f"  - Searching for missing books...")
        book_ids_for_author = [book['id'] for book in books_by_author[author_id]] # 'id' is bookId
        
        # Create detailed log with book titles
        book_details = []
        for book in books_by_author[author_id]:
            book_title = book.get('title', f"Book ID {book['id']}")
            book_details.append(f"'{book_title}' (ID: {book['id']})")
        
        # Construct detailed log message
        details_string = ', '.join(book_details)
        log_message = f"Triggering Book Search for {len(book_details)} books by author '{author_name}': [{details_string}]"
        readarr_logger.debug(log_message) # Changed level from INFO to DEBUG
        
        # Mark author as processed BEFORE triggering any searches
        add_processed_id("readarr", instance_name, str(author_id))
        readarr_logger.debug(f"Added author ID {author_id} to processed list for {instance_name}")
        
        # Now trigger the search
        search_command_result = readarr_api.search_books(api_url, api_key, book_ids_for_author, api_timeout)

        if search_command_result:
            # Extract command ID if the result is a dictionary, otherwise use the result directly
            command_id = search_command_result.get('id') if isinstance(search_command_result, dict) else search_command_result
            readarr_logger.info(f"Triggered book search command {command_id} for author {author_name}. Assuming success for now.") # Log only command ID
            increment_stat("readarr", "hunted")
            
            # Log to history system
            log_processed_media("readarr", author_name, author_id, instance_name, "missing")
            readarr_logger.debug(f"Logged history entry for author: {author_name}")
            
            processed_count += 1 # Count processed authors/groups
            processed_authors.append(author_name) # Add to list of processed authors
            processed_something = True
            readarr_logger.info(f"Processed {processed_count}/{len(authors_to_process)} authors/groups for missing books this cycle.")
        else:
            readarr_logger.error(f"Failed to trigger search for author {author_name}.")

        if processed_count >= hunt_missing_books:
            readarr_logger.info(f"Reached target of {hunt_missing_books} authors/groups processed for this cycle.")
            break

    if processed_authors:
        authors_list = '", "'.join(processed_authors)
        readarr_logger.info(f'Completed processing {processed_count} authors/groups for missing books this cycle: "{authors_list}"')
    else:
        readarr_logger.info(f"Completed processing {processed_count} authors/groups for missing books this cycle.")

    return processed_something