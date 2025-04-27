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
from typing import List, Callable, Dict, Optional, Any, Set # Add Any, Set
from src.primary.utils.logger import get_logger, debug_log
from src.primary import settings_manager
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.radarr.api import get_movies_with_missing, refresh_movie, movie_search
from src.primary.stats_manager import increment_stat  # Import the stats increment function

# Get app-specific logger
logger = get_logger("radarr")

def process_missing_movies(
    app_settings: Dict[str, Any], 
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process movies that are missing from the library.

    Args:
        app_settings: Dictionary containing settings for Radarr.
        stop_check: Function that returns True if processing should stop.

    Returns:
        True if any processing was done, False otherwise
    """
    # Get settings from the passed dictionary
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 60)
    hunt_missing_movies = app_settings.get("hunt_missing_movies", 1)
    random_missing = app_settings.get("random_missing", True)
    skip_movie_refresh = app_settings.get("skip_movie_refresh", False)
    monitored_only = app_settings.get("monitored_only", True) # Keep monitored_only logic if needed by API call
    skip_future_releases = app_settings.get("skip_future_releases", True)
    command_wait_delay = app_settings.get("command_wait_delay", 1)
    command_wait_attempts = app_settings.get("command_wait_attempts", 600)

    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("radarr", "processed_missing")

    logger.info("=== Checking for Missing Movies ===")

    if not api_url or not api_key:
        logger.error("API URL or Key not configured in settings. Cannot process missing movies.")
        return False

    # Skip if hunt_missing_movies is set to 0
    if hunt_missing_movies <= 0:
        logger.info("'hunt_missing_movies' setting is 0 or less. Skipping missing movie processing.")
        return False

    # Check for stop signal
    if stop_check():
        logger.info("Stop requested before starting missing movies. Aborting...")
        return False
    
    # Get missing movies (Assuming get_movies_with_missing uses settings_manager or needs update)
    # TODO: Update get_movies_with_missing if it needs api_url, api_key etc.
    logger.info("Retrieving movies with missing files...")
    # Pass necessary args if the API function requires them now
    missing_movies = get_movies_with_missing(api_url, api_key, api_timeout, monitored_only) 
    
    if missing_movies is None: # API call failed
        logger.error("Failed to retrieve missing movies from Radarr API.")
        return False
        
    if not missing_movies:
        logger.info("No missing movies found.")
        return False
    
    # Check for stop signal after retrieving movies
    if stop_check():
        logger.info("Stop requested after retrieving missing movies. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_movies)} movies with missing files.")
    
    # Filter out future releases if configured
    if skip_future_releases:
        now = datetime.datetime.now(datetime.timezone.utc)
        original_count = len(missing_movies)
        # Radarr movie object has 'inCinemas', 'physicalRelease' dates
        # Using 'physicalRelease' as the primary check, falling back if needed
        missing_movies = [
            movie for movie in missing_movies
            if movie.get('physicalRelease') and datetime.datetime.fromisoformat(movie['physicalRelease'].replace('Z', '+00:00')) < now
            # Add fallback or alternative logic if physicalRelease isn't always present
        ]
        skipped_count = original_count - len(missing_movies)
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} future movie releases based on physical release date.")

    if not missing_movies:
        logger.info("No missing movies left to process after filtering future releases.")
        return False
        
    processed_missing_ids: Set[int] = load_processed_ids(PROCESSED_MISSING_FILE)
    movies_processed = 0
    processing_done = False
    
    # Filter out already processed movies
    unprocessed_movies = [movie for movie in missing_movies if movie.get("id") not in processed_missing_ids]
    
    if not unprocessed_movies:
        logger.info("All available missing movies have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_movies)} missing movies that haven't been processed yet.")
    
    # Select movies to search based on configuration
    if random_missing:
        logger.info(f"Randomly selecting up to {hunt_missing_movies} missing movies.")
        movies_to_search = random.sample(unprocessed_movies, min(len(unprocessed_movies), hunt_missing_movies))
    else:
        logger.info(f"Selecting the first {hunt_missing_movies} missing movies (sorted by title).")
        # Sort by title for consistent ordering if not random
        unprocessed_movies.sort(key=lambda x: x.get("title", ""))
        movies_to_search = unprocessed_movies[:hunt_missing_movies]
    
    logger.info(f"Selected {len(movies_to_search)} missing movies to search.")

    processed_in_this_run = set()
    # Process selected movies
    for movie in movies_to_search:
        # Check for stop signal before each movie
        if stop_check():
            logger.info("Stop requested during movie processing. Aborting...")
            break
        
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_missing_movies", 1)
        if movies_processed >= current_limit:
             logger.info(f"Reached HUNT_MISSING_MOVIES limit ({current_limit}) for this cycle.")
             break

        movie_id = movie.get("id")
        title = movie.get("title", "Unknown Title")
        year = movie.get("year", "Unknown Year")
        
        logger.info(f"Processing missing movie: \"{title}\" ({year}) (Movie ID: {movie_id})")
        
        # Refresh the movie information if not skipped
        refresh_command_id = None
        if not skip_movie_refresh:
            logger.info(" - Refreshing movie information...")
            # Pass necessary args to refresh_movie
            refresh_command_id = refresh_movie(api_url, api_key, api_timeout, movie_id)
            if refresh_command_id:
                 # Assuming a wait_for_command function exists or needs to be added/imported
                 # if not wait_for_command(api_url, api_key, api_timeout, refresh_command_id, command_wait_delay, command_wait_attempts, "Movie Refresh", stop_check):
                 #    logger.warning(f"Movie refresh command (ID: {refresh_command_id}) did not complete successfully or timed out. Proceeding anyway.")
                 # Simple sleep for now if wait_for_command is not implemented for radarr
                 logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                 time.sleep(5) # Basic wait
            else:
                logger.warning(f"Failed to trigger refresh command for movie ID: {movie_id}. Proceeding without refresh.")
        else:
            logger.info(" - Skipping movie refresh (skip_movie_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the movie
        logger.info(" - Searching for missing movie...")
        # Pass necessary args to movie_search
        search_command_id = movie_search(api_url, api_key, api_timeout, [movie_id])
        if search_command_id:
            # Assuming a wait_for_command function exists or needs to be added/imported
            # if wait_for_command(api_url, api_key, api_timeout, search_command_id, command_wait_delay, command_wait_attempts, "Movie Search", stop_check):
            #    logger.info(f"Search command {search_command_id} completed successfully.")
            #    save_processed_id(PROCESSED_MISSING_FILE, movie_id)
            #    processed_in_this_run.add(movie_id)
            #    movies_processed += 1
            #    processing_done = True
            # else:
            #    logger.warning(f"Search command {search_command_id} did not complete successfully or timed out.")
            # Simple success log for now if wait_for_command is not implemented
            logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            save_processed_id(PROCESSED_MISSING_FILE, movie_id)
            processed_in_this_run.add(movie_id)
            movies_processed += 1
            processing_done = True
            
            # Increment the hunted statistics
            increment_stat("radarr", "hunted", 1)
            logger.debug(f"Incremented radarr hunted statistics by 1")

            # Log progress
            current_limit = app_settings.get("hunt_missing_movies", 1)
            logger.info(f"Processed {movies_processed}/{current_limit} missing movies this cycle.")
        else:
            logger.warning(f"Failed to trigger search command for movie ID {movie_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if processed_in_this_run:
        logger.info(f"Completed processing {len(processed_in_this_run)} missing movies for this cycle.")
    else:
        logger.info("No new missing movies were processed in this run.")
        
    # Consider if truncation should happen only if processing_done is True
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done