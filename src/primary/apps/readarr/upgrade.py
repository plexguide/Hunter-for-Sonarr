#!/usr/bin/env python3
"""
Quality Upgrade Processing for Readarr
Handles searching for books that need quality upgrades in Readarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
# Correct import path
from src.primary.utils.logger import get_logger
from src.primary import settings_manager
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.readarr.api import get_cutoff_unmet_books, refresh_author, book_search

# Get app-specific logger
logger = get_logger("readarr")

def process_cutoff_upgrades(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process books that need quality upgrades (cutoff unmet).
    
    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Get the current value directly at the start of processing
    # Use settings_manager directly instead of get_current_upgrade_limit
    HUNT_UPGRADE_BOOKS = settings_manager.get_setting("readarr", "hunt_upgrade_books", 0)
    RANDOM_UPGRADES = settings_manager.get_setting("readarr", "random_upgrades", True)
    SKIP_AUTHOR_REFRESH = settings_manager.get_setting("readarr", "skip_author_refresh", False)
    MONITORED_ONLY = settings_manager.get_setting("readarr", "monitored_only", True)
    
    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("readarr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if HUNT_UPGRADE_BOOKS is set to 0
    if HUNT_UPGRADE_BOOKS <= 0:
        logger.info("HUNT_UPGRADE_BOOKS is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get books needing quality upgrades
    logger.info("Retrieving books that need quality upgrades...")
    upgrade_books = get_cutoff_unmet_books()
    
    if not upgrade_books:
        logger.info("No books found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving books
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade books. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_books)} books that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    books_processed = 0
    processing_done = False
    
    # Filter out already processed books
    unprocessed_books = [book for book in upgrade_books if book.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_books:
        logger.info("All upgrade books have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_books)} upgrade books that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_UPGRADES:
        logger.info("Using random selection for quality upgrades (RANDOM_UPGRADES=true)")
        random.shuffle(unprocessed_books)
    else:
        logger.info("Using sequential selection for quality upgrades (RANDOM_UPGRADES=false)")
        # Sort by title for consistent ordering
        unprocessed_books.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing books
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing books. Aborting...")
        return False
    
    # Process up to HUNT_UPGRADE_BOOKS books
    for book in unprocessed_books:
        # Check for restart signal before each book
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during book processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        # Use settings_manager directly instead of get_current_upgrade_limit
        current_limit = settings_manager.get_setting("readarr", "hunt_upgrade_books", 0)
        
        if books_processed >= current_limit:
            logger.info(f"Reached HUNT_UPGRADE_BOOKS={current_limit} for this cycle.")
            break
        
        book_id = book.get("id")
        title = book.get("title", "Unknown Title")
        author_id = book.get("authorId")
        author_name = "Unknown Author"
        
        # Look for author name in the book
        if "author" in book and isinstance(book["author"], dict):
            author_name = book["author"].get("authorName", "Unknown Author")
        elif "author" in book and isinstance(book["author"], str):
            author_name = book["author"]
        
        # Get quality information
        quality_info = ""
        if "quality" in book and book["quality"]:
            quality_name = book["quality"].get("quality", {}).get("name", "Unknown")
            quality_info = f" (Current quality: {quality_name})"
        
        logger.info(f"Processing quality upgrade for: \"{title}\" by {author_name}{quality_info} (Book ID: {book_id})")
        
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
        logger.info(" - Searching for quality upgrade...")
        search_res = book_search([book_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, book_id)
            books_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            # Use settings_manager directly instead of get_current_upgrade_limit
            current_limit = settings_manager.get_setting("readarr", "hunt_upgrade_books", 0)
            logger.info(f"Processed {books_processed}/{current_limit} upgrade books this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for book ID {book_id}.")
            continue
    
    # Log final status
    # Use settings_manager directly instead of get_current_upgrade_limit
    current_limit = settings_manager.get_setting("readarr", "hunt_upgrade_books", 0)
    logger.info(f"Completed processing {books_processed} upgrade books for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done