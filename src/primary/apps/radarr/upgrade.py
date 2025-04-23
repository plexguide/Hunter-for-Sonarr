#!/usr/bin/env python3
"""
Quality Upgrade Processing for Radarr
Handles searching for movies that need quality upgrades in Radarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from primary.utils.logger import get_logger
from primary.config import MONITORED_ONLY
from primary import settings_manager
from primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from primary.apps.radarr.api import get_cutoff_unmet_movies, refresh_movie, movie_search

# Get app-specific logger
logger = get_logger("radarr")

def process_cutoff_upgrades(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process movies that need quality upgrades (cutoff unmet).
    
    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Get the current value directly at the start of processing
    # Use settings_manager directly instead of get_current_upgrade_limit
    HUNT_UPGRADE_MOVIES = settings_manager.get_setting("radarr", "hunt_upgrade_movies", 0)
    RANDOM_UPGRADES = settings_manager.get_setting("radarr", "random_upgrades", True)
    SKIP_MOVIE_REFRESH = settings_manager.get_setting("radarr", "skip_movie_refresh", False)
    MONITORED_ONLY = settings_manager.get_setting("radarr", "monitored_only", True)
    
    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("radarr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if HUNT_UPGRADE_MOVIES is set to 0
    if HUNT_UPGRADE_MOVIES <= 0:
        logger.info("HUNT_UPGRADE_MOVIES is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get movies needing quality upgrades
    logger.info("Retrieving movies that need quality upgrades...")
    upgrade_movies = get_cutoff_unmet_movies()
    
    if not upgrade_movies:
        logger.info("No movies found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving movies
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade movies. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_movies)} movies that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    movies_processed = 0
    processing_done = False
    
    # Filter out already processed movies
    unprocessed_movies = [movie for movie in upgrade_movies if movie.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_movies:
        logger.info("All upgrade movies have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_movies)} upgrade movies that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_UPGRADES:
        logger.info("Using random selection for quality upgrades (RANDOM_UPGRADES=true)")
        random.shuffle(unprocessed_movies)
    else:
        logger.info("Using sequential selection for quality upgrades (RANDOM_UPGRADES=false)")
        # Sort by title for consistent ordering
        unprocessed_movies.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing movies
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing movies. Aborting...")
        return False
    
    # Process up to HUNT_UPGRADE_MOVIES movies
    for movie in unprocessed_movies:
        # Check for restart signal before each movie
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during movie processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        # Use settings_manager directly instead of get_current_upgrade_limit
        current_limit = settings_manager.get_setting("radarr", "hunt_upgrade_movies", 0)
        
        if movies_processed >= current_limit:
            logger.info(f"Reached HUNT_UPGRADE_MOVIES={current_limit} for this cycle.")
            break
        
        movie_id = movie.get("id")
        title = movie.get("title", "Unknown Title")
        year = movie.get("year", "Unknown Year")
        
        # Get quality information
        quality_info = ""
        if "movieFile" in movie and movie["movieFile"]:
            quality = movie["movieFile"].get("quality", {})
            quality_name = quality.get("quality", {}).get("name", "Unknown")
            quality_info = f" (Current quality: {quality_name})"
        
        logger.info(f"Processing quality upgrade for: \"{title}\" ({year}){quality_info} (Movie ID: {movie_id})")
        
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
        logger.info(" - Searching for quality upgrade...")
        search_res = movie_search([movie_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, movie_id)
            movies_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            # Use settings_manager directly instead of get_current_upgrade_limit
            current_limit = settings_manager.get_setting("radarr", "hunt_upgrade_movies", 0)
            logger.info(f"Processed {movies_processed}/{current_limit} upgrade movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
            continue
    
    # Log final status
    # Use settings_manager directly instead of get_current_upgrade_limit
    current_limit = settings_manager.get_setting("radarr", "hunt_upgrade_movies", 0)
    logger.info(f"Completed processing {movies_processed} upgrade movies for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done