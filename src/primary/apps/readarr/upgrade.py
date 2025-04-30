#!/usr/bin/env python3
"""
Quality Upgrade Processing for Readarr
Handles searching for books that need quality upgrades in Readarr
"""

import time
import random
import datetime # Import the datetime module
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.readarr import api as readarr_api
from src.primary.stats_manager import increment_stat
from src.primary.stateful_manager import is_processed, add_processed_id

# Get logger for the app
readarr_logger = get_logger("readarr")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Readarr based on settings.
    
    Args:
        app_settings: Dictionary containing all settings for Readarr
        stop_check: A function that returns True if the process should stop
        
    Returns:
        True if any books were processed for upgrades, False otherwise.
    """
    readarr_logger.info("Starting quality cutoff upgrades processing cycle for Readarr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    instance_name = app_settings.get("instance_name", "Readarr Default")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_author_refresh = app_settings.get("skip_author_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    hunt_upgrade_books = app_settings.get("hunt_upgrade_books", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    
    # Get books eligible for upgrade
    readarr_logger.info("Retrieving books eligible for quality upgrade...")
    # Pass API credentials explicitly
    upgrade_eligible_data = readarr_api.get_cutoff_unmet_books(api_url=api_url, api_key=api_key, api_timeout=api_timeout)
    
    if upgrade_eligible_data is None: # Check if the API call failed (assuming it returns None on error)
        readarr_logger.error("Error retrieving books eligible for upgrade from Readarr API.")
        return False
    elif not upgrade_eligible_data: # Check if the list is empty
        readarr_logger.info("No books found eligible for upgrade.")
        return False
        
    readarr_logger.info(f"Found {len(upgrade_eligible_data)} books eligible for quality upgrade.")

    # Filter out future releases if configured
    skip_future_releases = app_settings.get("skip_future_releases", True)
    if skip_future_releases:
        now = datetime.datetime.now(datetime.timezone.utc)
        original_count = len(upgrade_eligible_data)
        filtered_books = []
        for book in upgrade_eligible_data:
            release_date_str = book.get('releaseDate')
            if release_date_str:
                try:
                    # Readarr release dates are usually just YYYY-MM-DD
                    release_date = datetime.datetime.strptime(release_date_str, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
                    if release_date <= now:
                        filtered_books.append(book)
                except ValueError:
                    readarr_logger.warning(f"Could not parse release date '{release_date_str}' for book ID {book.get('id')}. Including anyway.")
                    filtered_books.append(book)
            else:
                 filtered_books.append(book) # Include books without a release date

        upgrade_eligible_data = filtered_books
        skipped_count = original_count - len(upgrade_eligible_data)
        if skipped_count > 0:
            readarr_logger.info(f"Skipped {skipped_count} future books based on release date for upgrades.")

    if not upgrade_eligible_data:
        readarr_logger.info("No upgradeable books found to process (after potential filtering). Skipping.")
        return False
        
    # Filter out already processed books using stateful management
    unprocessed_books = []
    for book in upgrade_eligible_data:
        book_id = str(book.get("id"))
        if not is_processed("readarr", instance_name, book_id):
            unprocessed_books.append(book)
        else:
            readarr_logger.debug(f"Skipping already processed book ID: {book_id}")
    
    readarr_logger.info(f"Found {len(unprocessed_books)} unprocessed books out of {len(upgrade_eligible_data)} total books eligible for upgrade.")
    
    if not unprocessed_books:
        readarr_logger.info(f"No unprocessed books found for {instance_name}. All available books have been processed.")
        return False

    # Select books to process
    if random_upgrades:
        readarr_logger.info(f"Randomly selecting up to {hunt_upgrade_books} books for upgrade search.")
        books_to_process = random.sample(unprocessed_books, min(hunt_upgrade_books, len(unprocessed_books)))
    else:
        readarr_logger.info(f"Selecting the first {hunt_upgrade_books} books for upgrade search (order based on API return).")
        # Add sorting if needed, e.g., by title or author
        # upgrade_eligible_data.sort(key=lambda x: x.get('title', ''))
        books_to_process = unprocessed_books[:hunt_upgrade_books]

    readarr_logger.info(f"Selected {len(books_to_process)} books to search for upgrades.")
    processed_count = 0
    processed_something = False

    for book in books_to_process:
        if stop_check():
            readarr_logger.info("Stop signal received, aborting Readarr upgrade cycle.")
            break
            
        book_id = book.get("id")
        author_id = book.get("authorId") # Needed for refresh?
        book_title = book.get("title")
        
        readarr_logger.info(f"Processing upgrade for book: \"{book_title}\" (Book ID: {book_id})")

        # Refresh author (optional, check if needed for upgrades)
        # Ensure refresh_author also uses explicit credentials if it uses arr_request internally
        # Currently, refresh_author uses arr_request without passing credentials, let's fix that too.
        if not skip_author_refresh and author_id:
            readarr_logger.info(f"  - Refreshing author info (ID: {author_id})...")
            # Assuming refresh_author needs explicit credentials now
            refresh_result = readarr_api.refresh_author(author_id, api_url=api_url, api_key=api_key, api_timeout=api_timeout) 
            time.sleep(5) # Basic wait
            if not refresh_result:
                 readarr_logger.warning(f"  - Failed to trigger author refresh for {author_id}. Continuing search anyway.")
        elif skip_author_refresh:
             readarr_logger.info(f"  - Skipping author refresh (skip_author_refresh=true)")

        # Search for book upgrade
        # Ensure search_books uses explicit credentials (it already does)
        readarr_logger.info(f"  - Searching for upgrade for book...")
        search_command_data = readarr_api.search_books(api_url, api_key, [book_id], api_timeout) # Pass credentials

        if search_command_data:
            command_id = search_command_data.get('id') # Extract command ID
            readarr_logger.info(f"Triggered book search command {command_id} for upgrade.")
            increment_stat("readarr", "upgraded") # Assuming 'upgraded' stat exists
            
            # Add book ID to processed list
            add_processed_id("readarr", instance_name, str(book_id))
            readarr_logger.debug(f"Added book ID {book_id} to processed list for {instance_name}")
            
            processed_count += 1
            processed_something = True
            readarr_logger.info(f"Processed {processed_count}/{len(books_to_process)} book upgrades this cycle.")
        else:
            readarr_logger.error(f"Failed to trigger search for book {book_title} upgrade.")

        if processed_count >= hunt_upgrade_books:
            readarr_logger.info(f"Reached target of {hunt_upgrade_books} books processed for upgrade this cycle.")
            break

    readarr_logger.info(f"Completed processing {processed_count} books for upgrade this cycle.")
    
    return processed_something