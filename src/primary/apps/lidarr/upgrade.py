#!/usr/bin/env python3
"""
Lidarr cutoff upgrade processing module for Huntarr
Handles albums that do not meet the configured quality cutoff.
"""

import time
import random
import datetime
from typing import List, Dict, Any, Set, Callable 
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path
from src.primary.apps.lidarr import api as lidarr_api 
from src.primary.apps.lidarr.missing import wait_for_command # Reuse wait function
from src.primary.stats_manager import increment_stat  # Import the stats increment function

# Get logger for the Lidarr app
lidarr_logger = get_logger("lidarr")

# State file for processed upgrades (stores album IDs)
PROCESSED_UPGRADES_FILE = get_state_file_path("lidarr", "processed_upgrades")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any], 
    stop_check: Callable[[], bool] 
) -> bool: 
    """Process cutoff unmet albums in Lidarr for quality upgrades."""
    lidarr_logger.info("Starting cutoff upgrade processing cycle for Lidarr.")
    processed_any = False 

    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90) # Lidarr can be slower
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_artist_refresh = app_settings.get("skip_artist_refresh", False) # Reuse setting name
    random_upgrades = app_settings.get("random_upgrades", True) # Default random to True?
    # Use hunt_upgrade_items as the setting name
    hunt_upgrade_items = app_settings.get("hunt_upgrade_items", 0) 
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 120) # Increase wait for Lidarr?

    if not api_url or not api_key:
        lidarr_logger.error("API URL or Key not configured. Cannot process upgrades.")
        return False

    if hunt_upgrade_items <= 0:
        lidarr_logger.info("'hunt_upgrade_items' setting is 0 or less. Skipping upgrade processing.")
        return False

    # Load already processed album IDs for upgrades
    processed_upgrade_ids: Set[int] = set(load_processed_ids(PROCESSED_UPGRADES_FILE))
    lidarr_logger.debug(f"Loaded {len(processed_upgrade_ids)} processed upgrade album IDs for Lidarr.")

    # Get cutoff unmet albums from Lidarr API
    cutoff_unmet_albums = lidarr_api.get_cutoff_unmet_albums(api_url, api_key, api_timeout, monitored_only)
    if cutoff_unmet_albums is None: # API call failed
         lidarr_logger.error("Failed to get cutoff unmet albums from Lidarr API.")
         return False
         
    lidarr_logger.info(f"Received {len(cutoff_unmet_albums)} cutoff unmet albums from Lidarr API (after monitored filter if applied).")
    if not cutoff_unmet_albums:
        lidarr_logger.info("No cutoff unmet albums found in Lidarr requiring processing.")
        return False

    if stop_check(): lidarr_logger.info("Stop requested during upgrade processing."); return processed_any

    # Filter out already processed albums for upgrades
    albums_to_consider = [album for album in cutoff_unmet_albums if album['id'] not in processed_upgrade_ids]
    lidarr_logger.info(f"Found {len(albums_to_consider)} new cutoff unmet albums to process for upgrades.")

    # Filter out future releases if configured
    if skip_future_releases:
        now = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware comparison
        original_count = len(albums_to_consider)
        
        filtered_albums = []
        for album in albums_to_consider:
            release_date_str = album.get('releaseDate')
            if release_date_str:
                try:
                    # Handle both YYYY-MM-DD and ISO-8601 format with Z timezone
                    if 'T' in release_date_str:  # ISO-8601 format like 2014-06-10T00:00:00Z
                        # Remove the Z and parse with proper format
                        date_str = release_date_str.rstrip('Z')
                        release_date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
                    else:  # Simple date format YYYY-MM-DD
                        release_date = datetime.datetime.strptime(release_date_str, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
                    
                    if release_date < now:
                        filtered_albums.append(album)
                    # else: # Debug logging for skipped future albums
                    #     lidarr_logger.debug(f"Skipping future album ID {album.get('id')} ('{album.get('title')}') for upgrade with release date {release_date_str}")
                except ValueError as e:
                    lidarr_logger.warning(f"Could not parse release date '{release_date_str}' for upgrade album ID {album.get('id')}. Error: {e}. Including it anyway.")
                    filtered_albums.append(album)
            else:
                 filtered_albums.append(album) # Include albums without a release date

        albums_to_consider = filtered_albums
        skipped_count = original_count - len(albums_to_consider)
        if skipped_count > 0:
            lidarr_logger.info(f"Skipped {skipped_count} future albums based on release date for upgrades.")


    if not albums_to_consider:
        lidarr_logger.info("No cutoff unmet albums left to process for upgrades after filtering.")
        return False

    # Select albums to search based on configuration
    if random_upgrades:
        lidarr_logger.debug(f"Randomly selecting up to {hunt_upgrade_items} cutoff unmet albums for upgrade search.")
        albums_to_search = random.sample(albums_to_consider, min(len(albums_to_consider), hunt_upgrade_items))
    else:
        # Sort by release date? Or artist name? Let's stick to API order for now (artist name default)
        lidarr_logger.debug(f"Selecting the first {hunt_upgrade_items} cutoff unmet albums for upgrade search.")
        albums_to_search = albums_to_consider[:hunt_upgrade_items]

    album_ids_to_search = [album['id'] for album in albums_to_search]

    if not album_ids_to_search:
        lidarr_logger.info("No albums selected for upgrade search.")
        return False

    # Log more details about the selected albums for upgrade
    album_details = [f"{album.get('title', 'Unknown')} by {album.get('artist', {}).get('artistName', 'Unknown Artist')} (ID: {album['id']}, Quality: {album.get('quality', {}).get('quality', {}).get('name', 'Unknown')})" for album in albums_to_search]
    lidarr_logger.info(f"Selected {len(album_ids_to_search)} cutoff unmet albums to search for upgrades:")
    for album_detail in album_details:
        lidarr_logger.info(f" - {album_detail}")

    processed_in_this_run = set()

    # Optional: Refresh artists for selected albums before searching?
    if not skip_artist_refresh:
         artist_ids_to_refresh = {album['artistId'] for album in albums_to_search if album.get('artistId')}
         lidarr_logger.info(f"Refreshing {len(artist_ids_to_refresh)} artists related to selected upgrade albums (skip_artist_refresh=False).")
         for artist_id in artist_ids_to_refresh:
             if stop_check(): lidarr_logger.info("Stop requested during artist refresh for upgrades."); break
             lidarr_logger.debug(f"Attempting to refresh artist ID: {artist_id} before upgrade search.")
             refresh_command = lidarr_api.refresh_artist(api_url, api_key, api_timeout, artist_id)
             if refresh_command and refresh_command.get('id'):
                 # Don't wait excessively long
                 wait_for_command(api_url, api_key, api_timeout, refresh_command['id'], command_wait_delay, 10, f"RefreshArtist {artist_id} (Upgrade)", stop_check, log_success=False)
             else:
                 lidarr_logger.warning(f"Failed to trigger RefreshArtist command for artist ID: {artist_id} before upgrade search.")
         if stop_check(): lidarr_logger.info("Stop requested after artist refresh for upgrades."); return processed_any # Exit if stopped


    # Trigger Album Search for the selected batch
    lidarr_logger.debug(f"Attempting AlbumSearch for upgrade album IDs: {album_ids_to_search}")
    search_command = lidarr_api.search_albums(api_url, api_key, api_timeout, album_ids_to_search)

    if search_command and search_command.get('id'):
        if wait_for_command(
            api_url, api_key, api_timeout, search_command['id'],
            command_wait_delay, command_wait_attempts, f"AlbumSearch (Upgrade) {len(album_ids_to_search)} albums", stop_check
        ):
            # Mark albums as processed for upgrades if search command completed successfully
            processed_in_this_run.update(album_ids_to_search)
            processed_any = True 
            
            # Increment the upgraded statistics for Lidarr
            increment_stat("lidarr", "upgraded", len(album_ids_to_search))
            lidarr_logger.debug(f"Incremented lidarr upgraded statistics by {len(album_ids_to_search)}")
            
            lidarr_logger.info(f"Successfully processed upgrade search for {len(album_ids_to_search)} albums.")
        else:
            lidarr_logger.warning(f"Album upgrade search command (ID: {search_command['id']}) did not complete successfully or timed out. Albums will not be marked as processed for upgrades yet.")
    else:
        lidarr_logger.error(f"Failed to trigger upgrade search command (AlbumSearch) for albums {album_ids_to_search}.")

    # Update the set of processed upgrade album IDs and save to state file
    if processed_in_this_run:
        updated_processed_ids = processed_upgrade_ids.union(processed_in_this_run)
        save_processed_ids(PROCESSED_UPGRADES_FILE, list(updated_processed_ids))
        lidarr_logger.info(f"Saved {len(processed_in_this_run)} newly processed upgrade album IDs for Lidarr. Total processed for upgrades: {len(updated_processed_ids)}.")
    elif processed_any:
        lidarr_logger.info("Attempted upgrade processing, but no new albums were marked as successfully processed.")

    lidarr_logger.info("Finished cutoff upgrade processing cycle for Lidarr.")
    return processed_any