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
            should_include = False
            found_valid_date = False
            
            if release_date_str:
                try:
                    # Improved date parsing logic to handle various ISO formats
                    # Remove any milliseconds and normalize timezone
                    clean_date_str = release_date_str
                    
                    # Handle milliseconds (e.g., "2024-01-01T00:00:00.000Z")
                    if '.' in clean_date_str and 'Z' in clean_date_str:
                        clean_date_str = clean_date_str.split('.')[0] + 'Z'
                    
                    # Handle different timezone formats
                    if clean_date_str.endswith('Z'):
                        clean_date_str = clean_date_str[:-1] + '+00:00'
                    elif '+' not in clean_date_str and '-' not in clean_date_str[-6:]:
                        # No timezone info, assume UTC
                        clean_date_str += '+00:00'
                    
                    # Parse the release date
                    release_date = datetime.datetime.fromisoformat(clean_date_str)
                    found_valid_date = True
                    
                    if release_date <= now:
                        should_include = True
                    else:
                        radarr_logger.debug(f"Skipping future movie ID {movie.get('id')} ('{movie.get('title')}') with {release_type} release date: {release_date_str} (parsed as: {release_date})")
                        should_include = False
                except ValueError as e:
                    radarr_logger.warning(f"Could not parse {release_type} release date '{release_date_str}' for movie ID {movie.get('id')}. Error: {e}. Will check alternative dates.")
                    found_valid_date = False
            
            # If the specified release type field doesn't exist or couldn't be parsed, check alternative date fields
            if not found_valid_date:
                alternative_dates = []
                
                # Define all possible release date fields in order of preference
                all_date_fields = ['physicalRelease', 'digitalRelease', 'inCinemas', 'releaseDate']
                
                # Check alternative date fields (excluding the one we already tried)
                for alt_field in all_date_fields:
                    if alt_field != release_type_field:
                        alt_date_str = movie.get(alt_field)
                        if alt_date_str:
                            try:
                                # Use same parsing logic
                                clean_alt_date_str = alt_date_str
                                if '.' in clean_alt_date_str and 'Z' in clean_alt_date_str:
                                    clean_alt_date_str = clean_alt_date_str.split('.')[0] + 'Z'
                                if clean_alt_date_str.endswith('Z'):
                                    clean_alt_date_str = clean_alt_date_str[:-1] + '+00:00'
                                elif '+' not in clean_alt_date_str and '-' not in clean_alt_date_str[-6:]:
                                    clean_alt_date_str += '+00:00'
                                
                                alt_release_date = datetime.datetime.fromisoformat(clean_alt_date_str)
                                alternative_dates.append((alt_field, alt_release_date))
                            except ValueError:
                                # If we can't parse this alternative date, log it but continue
                                radarr_logger.debug(f"Could not parse {alt_field} date '{alt_date_str}' for movie ID {movie.get('id')}")
                                continue
                
                if alternative_dates:
                    # If we have alternative dates, use the earliest non-future one if available
                    # Otherwise, if ALL alternative dates are in the future, skip the movie
                    future_dates = []
                    past_dates = []
                    
                    for field_name, alt_date in alternative_dates:
                        if alt_date <= now:
                            past_dates.append((field_name, alt_date))
                        else:
                            future_dates.append((field_name, alt_date))
                    
                    if past_dates:
                        # At least one release date is in the past, include the movie
                        should_include = True
                        earliest_past = min(past_dates, key=lambda x: x[1])
                        radarr_logger.debug(f"Movie ID {movie.get('id')} ('{movie.get('title')}') has no {release_type_field} date, but {earliest_past[0]} date is in the past: {earliest_past[1]}, including in search")
                    else:
                        # All available dates are in the future, skip the movie  
                        should_include = False
                        earliest_future = min(future_dates, key=lambda x: x[1])
                        radarr_logger.debug(f"Skipping future movie ID {movie.get('id')} ('{movie.get('title')}') - all available release dates are in the future (earliest: {earliest_future[0]} on {earliest_future[1]})")
                        skipped_count += 1
                else:
                    # No valid release dates found at all, include in search to be safe
                    should_include = True
                    radarr_logger.warning(f"Movie ID {movie.get('id')} ('{movie.get('title')}') has no physicalRelease, digitalRelease, inCinemas, or releaseDate fields - including in search but this may indicate missing metadata in Radarr")
            
            if should_include:
                filtered_movies.append(movie)
            elif found_valid_date:  # Only increment skipped count if we found and used the specified date field
                skipped_count += 1
        
        missing_movies = filtered_movies
        if skipped_count > 0:
            radarr_logger.info(f"Skipped {skipped_count} future movie releases based on {release_type} release date.")
        
        radarr_logger.debug(f"After future release filtering: {len(missing_movies)} movies remaining from {original_count} original")

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
                    radarr_api.tag_processed_movie(api_url, api_key, api_timeout, movie_id, "huntarr-missing")
                    radarr_logger.debug(f"Tagged movie {movie_id} with 'huntarr-missing'")
                except Exception as e:
                    radarr_logger.warning(f"Failed to tag movie {movie_id} with 'huntarr-missing': {e}")
            
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