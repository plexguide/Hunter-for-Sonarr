#!/usr/bin/env python3
"""
Missing Movies Processing for Radarr
Handles searching for missing movies in Radarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from primary.utils.logger import get_logger, debug_log
from primary.config import MONITORED_ONLY
from primary import settings_manager
from primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from primary.apps.radarr.api import get_movies_with_missing, refresh_movie, movie_search

# Get app-specific logger
logger = get_logger("radarr")

def process_missing_movies(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process movies that are missing from the library.

    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle

    Returns:
        True if any processing was done, False otherwise
    """
    # Reload settings to ensure the latest values are used
    from primary.config import refresh_settings
    refresh_settings("radarr")

    # Get the current value directly at the start of processing
    HUNT_MISSING_MOVIES = settings_manager.get_setting("huntarr", "hunt_missing_movies", 1)
    RANDOM_MISSING = settings_manager.get_setting("advanced", "random_missing", True)
    SKIP_MOVIE_REFRESH = settings_manager.get_setting("advanced", "skip_movie_refresh", False)
    
    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("radarr", "processed_missing")

    logger.info("=== Checking for Missing Movies ===")

    # Skip if HUNT_MISSING_MOVIES is set to 0
    if HUNT_MISSING_MOVIES <= 0:
        logger.info("HUNT_MISSING_MOVIES is set to 0, skipping missing movies")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting missing movies. Aborting...")
        return False
    
    # Get missing movies
    logger.info("Retrieving movies with missing files...")
    missing_movies = get_movies_with_missing()
    
    if not missing_movies:
        logger.info("No missing movies found.")
        return False
    
    # Check for restart signal after retrieving movies
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving missing movies. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_movies)} movies with missing files.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    movies_processed = 0
    processing_done = False
    
    # Filter out already processed movies
    unprocessed_movies = [movie for movie in missing_movies if movie.get("id") not in processed_missing_ids]
    
    if not unprocessed_movies:
        logger.info("All missing movies have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_movies)} missing movies that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_MISSING:
        logger.info("Using random selection for missing movies (RANDOM_MISSING=true)")
        random.shuffle(unprocessed_movies)
    else:
        logger.info("Using sequential selection for missing movies (RANDOM_MISSING=false)")
        # Sort by title for consistent ordering
        unprocessed_movies.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing movies
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing movies. Aborting...")
        return False
    
    # Process up to HUNT_MISSING_MOVIES movies
    for movie in unprocessed_movies:
        # Check for restart signal before each movie
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during movie processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = settings_manager.get_setting("huntarr", "hunt_missing_movies", 1)
        
        if movies_processed >= current_limit:
            logger.info(f"Reached HUNT_MISSING_MOVIES={current_limit} for this cycle.")
            break
        
        movie_id = movie.get("id")
        title = movie.get("title", "Unknown Title")
        year = movie.get("year", "Unknown Year")
        
        logger.info(f"Processing missing movie: \"{title}\" ({year}) (Movie ID: {movie_id})")
        
        # Refresh the movie information if SKIP_MOVIE_REFRESH is false
        if not SKIP_MOVIE_REFRESH:
            logger.info(" - Refreshing movie information...")
            refresh_res = refresh_movie(movie_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this movie.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Radarr to process
            time.sleep(2)
        else:
            logger.info(" - Skipping movie refresh (SKIP_MOVIE_REFRESH=true)")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {title}. Aborting...")
            break
        
        # Search for the movie
        logger.info(" - Searching for missing movie...")
        search_res = movie_search([movie_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_MISSING_FILE, movie_id)
            movies_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = settings_manager.get_setting("huntarr", "hunt_missing_movies", 1)
            logger.info(f"Processed {movies_processed}/{current_limit} missing movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
            continue
    
    # Log final status
    current_limit = settings_manager.get_setting("huntarr", "hunt_missing_movies", 1)
    logger.info(f"Completed processing {movies_processed} missing movies for this cycle.")
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done