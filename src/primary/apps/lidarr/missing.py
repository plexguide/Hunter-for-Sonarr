#!/usr/bin/env python3
"""
Lidarr missing content processing module for Huntarr
Handles missing albums or artists based on configuration.
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
lidarr_logger = get_logger("lidarr")

def process_missing_albums(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing albums in Lidarr based on provided settings.

    Args:
        app_settings: Dictionary containing all settings for Lidarr.
        stop_check: A function that returns True if the process should stop.

    Returns:
        True if any albums were processed, False otherwise.
    """
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90) # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_artist_refresh = app_settings.get("skip_artist_refresh", False)
    hunt_missing_mode = app_settings.get("hunt_missing_mode", "album")
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_items = app_settings.get("hunt_missing_items", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)

    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    instance_name = app_settings.get("instance_name", "Default")
    lidarr_logger.info(f"Starting missing albums processing cycle for Lidarr.")

    hunt_missing_albums = app_settings.get("hunt_missing_albums", 0) # Assuming setting name
    if hunt_missing_albums <= 0:
        lidarr_logger.info(f"'hunt_missing_albums' is {hunt_missing_albums} or less. Skipping missing processing for {instance_name}.")
        return False

    api_timeout = app_settings.get("api_timeout", 120)
    monitored_only = app_settings.get("monitored_only", True)
    skip_artist_refresh = app_settings.get("skip_artist_refresh", True)
    random_missing = app_settings.get("random_missing", True)

    # Get missing albums
    lidarr_logger.info("Retrieving wanted/missing albums...")
    missing_albums_data = lidarr_api.get_wanted_missing(api_url, api_key, api_timeout, monitored_only)
    
    if not missing_albums_data:
        lidarr_logger.info("No missing albums found or error retrieving them.")
        return False
        
    lidarr_logger.info(f"Found {len(missing_albums_data)} missing albums.")

    unprocessed_albums = missing_albums_data

    if not unprocessed_albums:
        lidarr_logger.info("No missing albums found to process (after potential filtering). Skipping.")
        return False

    # Group by artist ID (optional, could process album by album)
    albums_by_artist = {}
    for album in unprocessed_albums:
        artist_id = album.get("artistId")
        if artist_id:
            if artist_id not in albums_by_artist:
                albums_by_artist[artist_id] = []
            albums_by_artist[artist_id].append(album)

    artist_ids = list(albums_by_artist.keys())

    # Select artists/albums to process
    if random_missing:
        lidarr_logger.info(f"Randomly selecting up to {hunt_missing_albums} artists with missing albums.")
        artists_to_process = random.sample(artist_ids, min(hunt_missing_albums, len(artist_ids)))
    else:
        lidarr_logger.info(f"Selecting the first {hunt_missing_albums} artists with missing albums (order based on API return).")
        artists_to_process = artist_ids[:hunt_missing_albums]

    lidarr_logger.info(f"Selected {len(artists_to_process)} artists to search for missing albums.")
    processed_count = 0
    processed_something = False

    for artist_id in artists_to_process:
        if stop_check():
            lidarr_logger.info("Stop signal received, aborting Lidarr missing cycle.")
            break

        artist_info = lidarr_api.get_artist_details(api_url, api_key, artist_id, api_timeout) # Assuming this exists
        artist_name = artist_info.get("artistName", f"Artist ID {artist_id}") if artist_info else f"Artist ID {artist_id}"
        
        lidarr_logger.info(f"Processing missing albums for artist: \"{artist_name}\" (Artist ID: {artist_id})")

        # Refresh artist (optional)
        if not skip_artist_refresh:
            lidarr_logger.info(f"  - Refreshing artist info...")
            refresh_result = lidarr_api.refresh_artist(api_url, api_key, artist_id, api_timeout) # Assuming this exists
            time.sleep(5) # Basic wait
            if not refresh_result:
                 lidarr_logger.warning(f"  - Failed to trigger artist refresh. Continuing search anyway.")
        else:
            lidarr_logger.info(f"  - Skipping artist refresh (skip_artist_refresh=true)")

        # Search for missing albums associated with the artist
        lidarr_logger.info(f"  - Searching for missing albums...")
        album_ids_for_artist = [album['albumId'] for album in albums_by_artist[artist_id]]
        search_command_id = lidarr_api.search_albums(api_url, api_key, album_ids_for_artist, api_timeout)

        if search_command_id:
            lidarr_logger.info(f"Triggered album search command {search_command_id} for artist {artist_name}. Assuming success for now.")
            increment_stat("lidarr", "hunted")
            processed_count += 1 # Count processed artists/groups
            processed_something = True
            lidarr_logger.info(f"Processed {processed_count}/{len(artists_to_process)} artists/groups for missing albums this cycle.")
        else:
            lidarr_logger.error(f"Failed to trigger search for artist {artist_name}.")

        if processed_count >= hunt_missing_albums:
            lidarr_logger.info(f"Reached target of {hunt_missing_albums} artists/groups processed for this cycle.")
            break

    lidarr_logger.info(f"Completed processing {processed_count} artists/groups for missing albums this cycle.")
    
    return processed_something