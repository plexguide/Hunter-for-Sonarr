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
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_author_refresh = app_settings.get("skip_author_refresh", False)
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_books = app_settings.get("hunt_missing_books", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)

    # Get missing books
    readarr_logger.info("Retrieving wanted/missing books...")
    missing_books_data = readarr_api.get_wanted_missing(api_url, api_key, api_timeout, monitored_only)
    
    if not missing_books_data:
        readarr_logger.info("No missing books found or error retrieving them.")
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

    # Select authors/books to process
    if random_missing:
        readarr_logger.info(f"Randomly selecting up to {hunt_missing_books} authors with missing books.")
        authors_to_process = random.sample(author_ids, min(hunt_missing_books, len(author_ids)))
    else:
        readarr_logger.info(f"Selecting the first {hunt_missing_books} authors with missing books (order based on API return).")
        authors_to_process = author_ids[:hunt_missing_books]

    readarr_logger.info(f"Selected {len(authors_to_process)} authors to search for missing books.")
    processed_count = 0
    processed_something = False

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
        search_command_id = readarr_api.search_books(api_url, api_key, book_ids_for_author, api_timeout)

        if search_command_id:
            readarr_logger.info(f"Triggered book search command {search_command_id} for author {author_name}. Assuming success for now.")
            increment_stat("readarr", "hunted")
            processed_count += 1 # Count processed authors/groups
            processed_something = True
            readarr_logger.info(f"Processed {processed_count}/{len(authors_to_process)} authors/groups for missing books this cycle.")
        else:
            readarr_logger.error(f"Failed to trigger search for author {author_name}.")

        if processed_count >= hunt_missing_books:
            readarr_logger.info(f"Reached target of {hunt_missing_books} authors/groups processed for this cycle.")
            break

    readarr_logger.info(f"Completed processing {processed_count} authors/groups for missing books this cycle.")
    
    return processed_something