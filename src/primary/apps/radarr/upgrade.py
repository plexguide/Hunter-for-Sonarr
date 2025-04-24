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
from typing import List, Callable, Dict, Optional, Any
# Correct import path
from src.primary.utils.logger import get_logger
from src.primary import settings_manager
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.radarr.api import get_cutoff_unmet_movies, refresh_movie, movie_search

# Get app-specific logger
logger = get_logger("radarr")

def process_cutoff_upgrades(app_settings: Dict[str, Any], restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process movies that need quality upgrades (cutoff unmet).
    
    Args:
        app_settings: Dictionary containing settings for Radarr.
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Get settings from the passed dictionary
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)
    hunt_upgrade_movies = app_settings.get("hunt_upgrade_movies", 0)
    random_upgrades = app_settings.get("random_upgrades", True)
    skip_movie_refresh = app_settings.get("skip_movie_refresh", False)
    monitored_only = app_settings.get("monitored_only", True)
    
    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("radarr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if hunt_upgrade_movies is set to 0
    if hunt_upgrade_movies <= 0:
        logger.info("hunt_upgrade_movies is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get movies needing quality upgrades
    logger.info("Retrieving movies that need quality upgrades...")
    upgrade_movies = get_cutoff_unmet_movies(api_url, api_key, api_timeout, monitored_only)
    
    if not upgrade_movies:
        logger.info("No movies found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving movies
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade movies. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_movies)} movies that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    
    # Filter out already processed movies
    unprocessed_movies = [movie for movie in upgrade_movies if movie.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_movies:
        logger.info("All upgrade movies have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_movies)} upgrade movies that haven't been processed yet.")
    
    # Randomize if requested
    if random_upgrades:
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
    
    # Create a list of movies to process, limited by hunt_upgrade_movies
    movies_to_process = unprocessed_movies[:min(len(unprocessed_movies), hunt_upgrade_movies)]
    
    # Log a summary of all movies that will be processed
    if movies_to_process:
        logger.info(f"Selected {len(movies_to_process)} movies for quality upgrades this cycle:")
        for idx, movie in enumerate(movies_to_process):
            title = movie.get("title", "Unknown Title")
            year = movie.get("year", "Unknown Year")
            movie_id = movie.get("id")
            quality_name = "Unknown"
            if "movieFile" in movie and movie["movieFile"]:
                quality = movie["movieFile"].get("quality", {})
                quality_name = quality.get("quality", {}).get("name", "Unknown")
            logger.info(f" {idx+1}. \"{title}\" ({year}) - Current quality: {quality_name} (ID: {movie_id})")
    
    # Process up to hunt_upgrade_movies movies
    movies_processed = 0
    processing_done = False
    for movie in movies_to_process:
        # Check for restart signal before each movie
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during movie processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = app_settings.get("hunt_upgrade_movies", 0)
        
        if movies_processed >= current_limit:
            logger.info(f"Reached hunt_upgrade_movies={current_limit} for this cycle.")
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
        
        # Refresh the movie information if skip_movie_refresh is false
        if not skip_movie_refresh:
            logger.info(" - Refreshing movie information...")
            refresh_res = refresh_movie(api_url, api_key, api_timeout, movie_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this movie.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Radarr to process
            time.sleep(2)
        else:
            logger.info(" - Skipping movie refresh (skip_movie_refresh=true)")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {title}. Aborting...")
            break
        
        # Search for the movie
        logger.info(" - Searching for quality upgrade...")
        search_res = movie_search(api_url, api_key, api_timeout, [movie_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, movie_id)
            movies_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = app_settings.get("hunt_upgrade_movies", 0)
            logger.info(f"Processed {movies_processed}/{current_limit} upgrade movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
            continue
    
    # Log final status
    current_limit = app_settings.get("hunt_upgrade_movies", 0)
    logger.info(f"Completed processing {movies_processed} upgrade movies this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done