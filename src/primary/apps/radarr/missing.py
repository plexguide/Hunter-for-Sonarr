#!/usr/bin/env python3
"""
Missing Movies Processing for Radarr
Handles searching for missing movies in Radarr
"""

import os
import time
import random
import datetime
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.radarr import api as radarr_api
from src.primary.stats_manager import increment_stat_only
from src.primary.stateful_manager import is_processed, add_processed_id
from src.primary.utils.history_utils import log_processed_media
from src.primary.settings_manager import load_settings, get_advanced_setting

# Get logger for the app
radarr_logger = get_logger("radarr")

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
    processed_any = False
    
    # Get instance name - check for instance_name first, fall back to legacy "name" key if needed
    instance_name = app_settings.get("instance_name", app_settings.get("name", "Radarr Default"))
    
    # Load settings to check if tagging is enabled
    radarr_settings = load_settings("radarr")
    tag_processed_items = radarr_settings.get("tag_processed_items", True)
    
    # Log important settings
    radarr_logger.info("=== Radarr Missing Movies Settings ===")
    radarr_logger.debug(f"Instance Name: {instance_name}")
    
    # Extract necessary settings
    api_url = app_settings.get("api_url", "").strip()
    api_key = app_settings.get("api_key", "").strip()
    api_timeout = get_advanced_setting("api_timeout", 120)  # Use general.json value
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    # skip_movie_refresh setting removed as it was a performance bottleneck
    hunt_missing_movies = app_settings.get("hunt_missing_movies", 0)
    
    # Use advanced settings from general.json for command operations
    command_wait_delay = get_advanced_setting("command_wait_delay", 1)
    command_wait_attempts = get_advanced_setting("command_wait_attempts", 600)
    release_type = app_settings.get("release_type", "physical")
    
    radarr_logger.info(f"Hunt Missing Movies: {hunt_missing_movies}")
    radarr_logger.info(f"Monitored Only: {monitored_only}")
    radarr_logger.info(f"Skip Future Releases: {skip_future_releases}")
    # Skip Movie Refresh setting has been removed
    radarr_logger.info(f"Release Type for Future Status: {release_type}")
    
    release_type_field = 'physicalRelease'
    if release_type == 'digital':
        release_type_field = 'digitalRelease'
    elif release_type == 'cinema':
        release_type_field = 'inCinemas'
        
    radarr_logger.info(f"Using {release_type_field} date to determine future releases")
    radarr_logger.info("=======================================")
    
    radarr_logger.info("Starting missing movies processing cycle for Radarr.")
    
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
    
    # Get missing movies 
    radarr_logger.info("Retrieving movies with missing files...")
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
        now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        original_count = len(missing_movies)
        
        filtered_movies = []
        skipped_count = 0
        for movie in missing_movies:
            release_date_str = movie.get(release_type_field)
            if release_date_str:
                try:
                    # Parse the release date
                    release_date = datetime.datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
                    if release_date <= now:
                        filtered_movies.append(movie)
                    else:
                        radarr_logger.debug(f"Skipping future movie ID {movie.get('id')} ('{movie.get('title')}') with {release_type} release date: {release_date_str}")
                        skipped_count += 1
                except ValueError as e:
                    radarr_logger.warning(f"Could not parse {release_type} release date '{release_date_str}' for movie ID {movie.get('id')}. Error: {e}. Including it.")
                    filtered_movies.append(movie)  # Keep if date is invalid
            else:
                filtered_movies.append(movie)  # Keep if no release date
        
        missing_movies = filtered_movies
        if skipped_count > 0:
            radarr_logger.info(f"Skipped {skipped_count} future movie releases based on {release_type} release date.")

    if not missing_movies:
        radarr_logger.info("No missing movies left to process after filtering future releases.")
        return False
        
    movies_processed = 0
    processing_done = False
    
    # Filter out already processed movies using stateful management
    unprocessed_movies = []
    for movie in missing_movies:
        movie_id = str(movie.get("id"))
        if not is_processed("radarr", instance_name, movie_id):
            unprocessed_movies.append(movie)
        else:
            radarr_logger.debug(f"Skipping already processed movie ID: {movie_id}")
    
    radarr_logger.info(f"Found {len(unprocessed_movies)} unprocessed missing movies out of {len(missing_movies)} total.")
    
    if not unprocessed_movies:
        radarr_logger.info("No unprocessed missing movies found. All available movies have been processed.")
        return False
    
    # Always use random selection for missing movies
    radarr_logger.info(f"Using random selection for missing movies")
    if len(unprocessed_movies) > hunt_missing_movies:
        movies_to_process = random.sample(unprocessed_movies, hunt_missing_movies)
    else:
        movies_to_process = unprocessed_movies
    
    radarr_logger.info(f"Selected {len(movies_to_process)} movies to process.")
    
    # Add detailed logging for selected movies
    if movies_to_process:
        radarr_logger.info(f"Movies selected for processing in this cycle:")
        for idx, movie in enumerate(movies_to_process):
            movie_id = movie.get("id")
            movie_title = movie.get("title", "Unknown Title")
            year = movie.get("year", "Unknown Year")
            radarr_logger.info(f"  {idx+1}. {movie_title} ({year}) - ID: {movie_id}")
    
    # Process each movie
    for movie in movies_to_process:
        if stop_check():
            radarr_logger.info("Stop requested during processing. Aborting...")
            break
            
        movie_id = movie.get("id")
        movie_title = movie.get("title", "Unknown Title")
        
        # Refresh functionality has been removed as it was identified as a performance bottleneck
        
        # Search for the movie
        radarr_logger.info(f"Searching for movie '{movie_title}' (ID: {movie_id})...")
        search_success = radarr_api.movie_search(api_url, api_key, api_timeout, [movie_id])
        
        if search_success:
            radarr_logger.info(f"Successfully triggered search for movie '{movie_title}'")
            
            # Tag the movie if enabled
            if tag_processed_items:
                try:
                    radarr_api.tag_processed_movie(api_url, api_key, api_timeout, movie_id)
                    radarr_logger.debug(f"Tagged movie {movie_id} as processed")
                except Exception as e:
                    radarr_logger.warning(f"Failed to tag movie {movie_id}: {e}")
            
            # Immediately add to processed IDs to prevent duplicate processing
            success = add_processed_id("radarr", instance_name, str(movie_id))
            radarr_logger.debug(f"Added processed ID: {movie_id}, success: {success}")
            
            # Log to history system
            year = movie.get("year", "Unknown Year")
            media_name = f"{movie_title} ({year})"
            log_processed_media("radarr", media_name, movie_id, instance_name, "missing")
            radarr_logger.debug(f"Logged history entry for movie: {media_name}")
            
            increment_stat_only("radarr", "hunted")
            movies_processed += 1
            processed_any = True
        else:
            radarr_logger.warning(f"Failed to trigger search for movie '{movie_title}'")
    
    radarr_logger.info(f"Finished processing missing movies. Processed {movies_processed} of {len(movies_to_process)} selected movies.")
    return processed_any