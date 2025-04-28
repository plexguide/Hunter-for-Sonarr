#!/usr/bin/env python3
"""
Missing Movies Processing for Radarr
Handles searching for missing movies in Radarr
"""

import time
import random
import datetime
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path, truncate_processed_list
from src.primary.apps.radarr import api as radarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
radarr_logger = get_logger("radarr")

# State file for processed missing movies
PROCESSED_MISSING_FILE = get_state_file_path("radarr", "processed_missing")

def process_missing_movies(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing movies in Radarr based on provided settings.
    
    Args:
        app_settings: Dictionary containing all settings for Radarr
        stop_check: A function that returns True if the process should stop
    
    Returns:
        True if any movies were processed, False otherwise.
    """
    radarr_logger.info("Starting missing movies processing cycle for Radarr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_movie_refresh = app_settings.get("skip_movie_refresh", False)
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_movies = app_settings.get("hunt_missing_movies", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  # Add this line to get the stateful reset interval

    if not api_url or not api_key:
        radarr_logger.error("API URL or Key not configured in settings. Cannot process missing movies.")
        return False

    # Skip if hunt_missing_movies is set to 0
    if hunt_missing_movies <= 0:
        radarr_logger.info("'hunt_missing_movies' setting is 0 or less. Skipping missing movie processing.")
        return False

    # Check for stop signal
    if stop_check():
        radarr_logger.info("Stop requested before starting missing movies. Aborting...")
        return False
    
    # Get missing movies (Assuming get_movies_with_missing uses settings_manager or needs update)
    # TODO: Update get_movies_with_missing if it needs api_url, api_key etc.
    radarr_logger.info("Retrieving movies with missing files...")
    # Pass necessary args if the API function requires them now
    missing_movies = radarr_api.get_movies_with_missing(api_url, api_key, api_timeout, monitored_only) 
    
    if missing_movies is None: # API call failed
        radarr_logger.error("Failed to retrieve missing movies from Radarr API.")
        return False
        
    if not missing_movies:
        radarr_logger.info("No missing movies found.")
        return False
    
    # Check for stop signal after retrieving movies
    if stop_check():
        radarr_logger.info("Stop requested after retrieving missing movies. Aborting...")
        return False
    
    radarr_logger.info(f"Found {len(missing_movies)} movies with missing files.")
    
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
            radarr_logger.info(f"Skipped {skipped_count} future movie releases based on physical release date.")

    if not missing_movies:
        radarr_logger.info("No missing movies left to process after filtering future releases.")
        return False
        
    processed_missing_ids: Set[int] = load_processed_ids(PROCESSED_MISSING_FILE)
    movies_processed = 0
    processing_done = False
    
    # Filter out already processed movies
    unprocessed_movies = [movie for movie in missing_movies if movie.get("id") not in processed_missing_ids]
    
    if not unprocessed_movies:
        radarr_logger.info("All available missing movies have already been processed. Skipping.")
        return False
    
    radarr_logger.info(f"Found {len(unprocessed_movies)} missing movies that haven't been processed yet.")
    
    # Select movies to search based on configuration
    if random_missing:
        radarr_logger.info(f"Randomly selecting up to {hunt_missing_movies} missing movies.")
        movies_to_search = random.sample(unprocessed_movies, min(len(unprocessed_movies), hunt_missing_movies))
    else:
        radarr_logger.info(f"Selecting the first {hunt_missing_movies} missing movies (sorted by title).")
        # Sort by title for consistent ordering if not random
        unprocessed_movies.sort(key=lambda x: x.get("title", ""))
        movies_to_search = unprocessed_movies[:hunt_missing_movies]
    
    radarr_logger.info(f"Selected {len(movies_to_search)} missing movies to search.")

    processed_in_this_run = set()
    # Process selected movies
    for movie in movies_to_search:
        # Check for stop signal before each movie
        if stop_check():
            radarr_logger.info("Stop requested during movie processing. Aborting...")
            break
        
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_missing_movies", 1)
        if movies_processed >= current_limit:
             radarr_logger.info(f"Reached HUNT_MISSING_MOVIES limit ({current_limit}) for this cycle.")
             break

        movie_id = movie.get("id")
        title = movie.get("title", "Unknown Title")
        year = movie.get("year", "Unknown Year")
        
        radarr_logger.info(f"Processing missing movie: \"{title}\" ({year}) (Movie ID: {movie_id})")
        
        # Refresh the movie information if not skipped
        refresh_command_id = None
        if not skip_movie_refresh:
            radarr_logger.info(" - Refreshing movie information...")
            # Pass necessary args to refresh_movie
            refresh_command_id = radarr_api.refresh_movie(api_url, api_key, api_timeout, movie_id)
            if refresh_command_id:
                 # Assuming a wait_for_command function exists or needs to be added/imported
                 # if not wait_for_command(api_url, api_key, api_timeout, refresh_command_id, command_wait_delay, command_wait_attempts, "Movie Refresh", stop_check):
                 #    radarr_logger.warning(f"Movie refresh command (ID: {refresh_command_id}) did not complete successfully or timed out. Proceeding anyway.")
                 # Simple sleep for now if wait_for_command is not implemented for radarr
                 radarr_logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                 time.sleep(5) # Basic wait
            else:
                radarr_logger.warning(f"Failed to trigger refresh command for movie ID: {movie_id}. Proceeding without refresh.")
        else:
            radarr_logger.info(" - Skipping movie refresh (skip_movie_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            radarr_logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the movie
        radarr_logger.info(" - Searching for missing movie...")
        # Pass necessary args to movie_search
        search_command_id = radarr_api.movie_search(api_url, api_key, api_timeout, [movie_id])
        if search_command_id:
            # Assuming a wait_for_command function exists or needs to be added/imported
            # if wait_for_command(api_url, api_key, api_timeout, search_command_id, command_wait_delay, command_wait_attempts, "Movie Search", stop_check):
            #    radarr_logger.info(f"Search command {search_command_id} completed successfully.")
            #    save_processed_id(PROCESSED_MISSING_FILE, movie_id)
            #    processed_in_this_run.add(movie_id)
            #    movies_processed += 1
            #    processing_done = True
            # else:
            #    radarr_logger.warning(f"Search command {search_command_id} did not complete successfully or timed out.")
            # Simple success log for now if wait_for_command is not implemented
            radarr_logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            save_processed_ids(PROCESSED_MISSING_FILE, movie_id)
            processed_in_this_run.add(movie_id)
            movies_processed += 1
            processing_done = True
            
            # Increment the hunted statistics
            increment_stat("radarr", "hunted", 1)
            radarr_logger.debug(f"Incremented radarr hunted statistics by 1")

            # Log progress
            current_limit = app_settings.get("hunt_missing_movies", 1)
            radarr_logger.info(f"Processed {movies_processed}/{current_limit} missing movies this cycle.")
        else:
            radarr_logger.warning(f"Failed to trigger search command for movie ID {movie_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if processed_in_this_run:
        radarr_logger.info(f"Completed processing {len(processed_in_this_run)} missing movies for this cycle.")
    else:
        radarr_logger.info("No new missing movies were processed in this run.")
        
    # Consider if truncation should happen only if processing_done is True
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done