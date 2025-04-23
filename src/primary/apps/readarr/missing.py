#!/usr/bin/env python3
"""
Missing Books Processing for Readarr
Handles searching for missing books in Readarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from src.primary.utils.logger import get_logger, debug_log
from src.primary.config import MONITORED_ONLY
from src.primary import settings_manager
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.readarr.api import get_books_with_missing_files, refresh_author, book_search

# Get app-specific logger
logger = get_logger("readarr")

def process_missing_books(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process books that are missing from the library.

    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle

    Returns:
        True if any processing was done, False otherwise
    """
    # Removed refresh_settings call

    # Get the current value directly at the start of processing
    HUNT_MISSING_BOOKS = settings_manager.get_setting("readarr", "hunt_missing_books", 1)
    RANDOM_MISSING = settings_manager.get_setting("readarr", "random_missing", True)
    SKIP_AUTHOR_REFRESH = settings_manager.get_setting("readarr", "skip_author_refresh", False)
    MONITORED_ONLY = settings_manager.get_setting("readarr", "monitored_only", True)

    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("readarr", "processed_missing")

    logger.info("=== Checking for Missing Books ===")

    # Skip if HUNT_MISSING_BOOKS is set to 0
    if HUNT_MISSING_BOOKS <= 0:
        logger.info("HUNT_MISSING_BOOKS is set to 0, skipping missing books")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting missing books. Aborting...")
        return False
    
    # Get missing books
    logger.info("Retrieving books with missing files...")
    missing_books = get_books_with_missing_files()
    
    if not missing_books:
        logger.info("No missing books found.")
        return False
    
    # Check for restart signal after retrieving books
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving missing books. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_books)} books with missing files.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    books_processed = 0
    processing_done = False
    
    # Filter out already processed books
    unprocessed_books = [book for book in missing_books if book.get("id") not in processed_missing_ids]
    
    if not unprocessed_books:
        logger.info("All missing books have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_books)} missing books that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_MISSING:
        logger.info("Using random selection for missing books (RANDOM_MISSING=true)")
        random.shuffle(unprocessed_books)
    else:
        logger.info("Using sequential selection for missing books (RANDOM_MISSING=false)")
        # Sort by title for consistent ordering
        unprocessed_books.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing books
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing books. Aborting...")
        return False
    
    # Process up to HUNT_MISSING_BOOKS books
    for book in unprocessed_books:
        # Check for restart signal before each book
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during book processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = settings_manager.get_setting("readarr", "hunt_missing_books", 1)
        
        if books_processed >= current_limit:
            logger.info(f"Reached HUNT_MISSING_BOOKS={current_limit} for this cycle.")
            break
        
        book_id = book.get("id")
        title = book.get("title", "Unknown Title")
        author_id = book.get("authorId")
        author_name = "Unknown Author"
        
        # Look for author name in the book
        if "author" in book and isinstance(book["author"], dict):
            author_name = book["author"].get("authorName", "Unknown Author")
        
        # Get release date or publication year
        release_date = "Unknown"
        if "releaseDate" in book:
            release_date = book.get("releaseDate", "Unknown")
        
        logger.info(f"Processing missing book: \"{title}\" by {author_name} (Released: {release_date}) (Book ID: {book_id})")
        
        # Refresh the author information if SKIP_AUTHOR_REFRESH is false
        if not SKIP_AUTHOR_REFRESH and author_id is not None:
            logger.info(" - Refreshing author information...")
            refresh_res = refresh_author(author_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this book.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Readarr to process
            time.sleep(2)
        else:
            reason = "SKIP_AUTHOR_REFRESH=true" if SKIP_AUTHOR_REFRESH else "author_id is None"
            logger.info(f" - Skipping author refresh ({reason})")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {title}. Aborting...")
            break
        
        # Search for the book
        logger.info(" - Searching for missing book...")
        search_res = book_search([book_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_MISSING_FILE, book_id)
            books_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = settings_manager.get_setting("readarr", "hunt_missing_books", 1)
            logger.info(f"Processed {books_processed}/{current_limit} missing books this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for book ID {book_id}.")
            continue
    
    # Log final status
    current_limit = settings_manager.get_setting("readarr", "hunt_missing_books", 1)
    logger.info(f"Completed processing {books_processed} missing books for this cycle.")
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done