#!/usr/bin/env python3
"""
Lidarr missing content processing module for Huntarr
Handles missing albums or artists based on configuration.
"""

import time
import random
import datetime # Import datetime
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.stats_manager import increment_stat  # Import the stats increment function

# Get logger for the Lidarr app
lidarr_logger = get_logger("lidarr")

# State file for processed missing items
PROCESSED_MISSING_FILE = get_state_file_path("lidarr", "processed_missing") 

def process_missing_content(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing content (albums or artists) in Lidarr based on settings.

    Args:
        app_settings: Dictionary containing all settings for Lidarr.
        stop_check: A function that returns True if the process should stop.

    Returns:
        True if any items were processed, False otherwise.
    """
    lidarr_logger.info("Starting missing content processing cycle for Lidarr.")
    processed_any = False

    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90) # Lidarr can be slower
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_artist_refresh = app_settings.get("skip_artist_refresh", False)
    random_missing = app_settings.get("random_missing", True) # Default random to True for Lidarr?
    hunt_missing_items = app_settings.get("hunt_missing_items", 0) 
    # Get the missing hunt mode, default to 'artist' as requested
    hunt_missing_mode = app_settings.get("hunt_missing_mode", "artist").lower()
    # Get command wait settings
    command_wait_delay = app_settings.get("command_wait_delay", 1)
    command_wait_attempts = app_settings.get("command_wait_attempts", 600)

    if not api_url or not api_key:
        lidarr_logger.error("API URL or Key not configured. Cannot process missing content.")
        return False

    if hunt_missing_items <= 0:
        lidarr_logger.info("'hunt_missing_items' setting is 0 or less. Skipping missing content processing.")
        return False
        
    if hunt_missing_mode not in ['artist', 'album']:
        lidarr_logger.error(f"Invalid 'hunt_missing_mode': {hunt_missing_mode}. Must be 'artist' or 'album'. Skipping.")
        return False

    lidarr_logger.info(f"Processing missing content in '{hunt_missing_mode}' mode.")

    # Load already processed album IDs (even in artist mode, we mark albums)
    processed_album_ids: Set[int] = set(load_processed_ids(PROCESSED_MISSING_FILE))
    lidarr_logger.debug(f"Loaded {len(processed_album_ids)} processed missing album IDs for Lidarr.")

    # Get missing albums from Lidarr API
    missing_albums = lidarr_api.get_missing_albums(api_url, api_key, api_timeout, monitored_only)
    if missing_albums is None: # API call failed
         lidarr_logger.error("Failed to get missing albums from Lidarr API.")
         return False
         
    lidarr_logger.info(f"Received {len(missing_albums)} missing albums from Lidarr API (after monitored filter if applied).")
    if not missing_albums:
        lidarr_logger.info("No missing albums found in Lidarr requiring processing.")
        return False

    if stop_check(): lidarr_logger.info("Stop requested during missing content processing."); return processed_any

    # Filter out already processed albums
    albums_to_consider = [album for album in missing_albums if album['id'] not in processed_album_ids]
    lidarr_logger.info(f"Found {len(albums_to_consider)} new missing albums to consider.")

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
                    #     lidarr_logger.debug(f"Skipping future album ID {album.get('id')} ('{album.get('title')}') with release date {release_date_str}")
                except ValueError as e:
                    lidarr_logger.warning(f"Could not parse release date '{release_date_str}' for album ID {album.get('id')}. Error: {e}. Including it anyway.")
                    filtered_albums.append(album) # Include if date is invalid
            else:
                 filtered_albums.append(album) # Include albums without a release date

        albums_to_consider = filtered_albums
        skipped_count = original_count - len(albums_to_consider)
        if skipped_count > 0:
            lidarr_logger.info(f"Skipped {skipped_count} future albums based on release date.")

    if not albums_to_consider:
        lidarr_logger.info("No missing albums left to process after filtering.")
        return False

    processed_in_this_run = set()

    # --- Artist Mode ---
    if hunt_missing_mode == 'artist':
        lidarr_logger.info(f"Processing in 'artist' mode. Selecting up to {hunt_missing_items} artists with missing albums.")
        
        # Group albums by artist ID
        artists_with_missing: Dict[int, List[Dict]] = {}
        artist_names: Dict[int, str] = {}
        
        for album in albums_to_consider:
            artist_id = album.get('artistId')
            if artist_id:
                if artist_id not in artists_with_missing:
                    artists_with_missing[artist_id] = []
                    artist_names[artist_id] = album.get('artist', {}).get('artistName', f"Artist ID {artist_id}")
                artists_with_missing[artist_id].append(album)
        
        if not artists_with_missing:
             lidarr_logger.info("No artists found with new missing albums to process.")
             return False

        # Select artists to process
        artist_ids_to_process = list(artists_with_missing.keys())
        if random_missing:
            lidarr_logger.debug(f"Randomly selecting artists.")
            random.shuffle(artist_ids_to_process)
            
        artists_to_search = artist_ids_to_process[:hunt_missing_items]
        lidarr_logger.info(f"Selected {len(artists_to_search)} artists to search.")

        # Process selected artists
        for artist_id in artists_to_search:
            if stop_check(): lidarr_logger.info("Stop requested before processing next artist."); break
            
            artist_name = artist_names.get(artist_id, f"Artist ID {artist_id}")
            missing_albums_for_artist = artists_with_missing[artist_id]
            missing_album_ids_for_artist = {album['id'] for album in missing_albums_for_artist}
            lidarr_logger.info(f"Processing artist: {artist_name} (ID: {artist_id}) with {len(missing_albums_for_artist)} missing albums.")

            # 1. Refresh Artist (optional)
            refresh_command = None
            if not skip_artist_refresh:
                lidarr_logger.debug(f"Attempting to refresh artist ID: {artist_id}")
                refresh_command = lidarr_api.refresh_artist(api_url, api_key, api_timeout, artist_id)
                if refresh_command and refresh_command.get('id'):
                    if not wait_for_command(
                        api_url, api_key, api_timeout, refresh_command['id'],
                        command_wait_delay, command_wait_attempts, f"RefreshArtist {artist_id}", stop_check
                    ):
                        lidarr_logger.warning(f"RefreshArtist command (ID: {refresh_command['id']}) for artist {artist_id} did not complete successfully or timed out. Proceeding anyway.")
                else:
                     lidarr_logger.warning(f"Failed to trigger RefreshArtist command for artist ID: {artist_id}. Proceeding without refresh.")
            else:
                lidarr_logger.debug(f"Skipping artist refresh for artist ID: {artist_id} as configured.")

            if stop_check(): lidarr_logger.info("Stop requested after artist refresh attempt."); break

            # 2. Trigger Artist Search
            lidarr_logger.debug(f"Attempting ArtistSearch for artist ID: {artist_id}")
            search_command = lidarr_api.search_artist(api_url, api_key, api_timeout, artist_id)

            if search_command and search_command.get('id'):
                if wait_for_command(
                    api_url, api_key, api_timeout, search_command['id'],
                    command_wait_delay, command_wait_attempts, f"ArtistSearch {artist_id}", stop_check
                ):
                    # Mark all initially identified missing albums for this artist as processed
                    processed_in_this_run.update(missing_album_ids_for_artist)
                    processed_any = True
                    
                    # Increment the hunted statistics for Lidarr
                    increment_stat("lidarr", "hunted", len(missing_album_ids_for_artist))
                    lidarr_logger.debug(f"Incremented lidarr hunted statistics by {len(missing_album_ids_for_artist)}")
                    
                    lidarr_logger.info(f"Successfully processed ArtistSearch for artist {artist_id}. Marked {len(missing_album_ids_for_artist)} related albums as processed.")
                else:
                    lidarr_logger.warning(f"ArtistSearch command (ID: {search_command['id']}) for artist {artist_id} did not complete successfully or timed out. Albums will not be marked as processed yet.")
            else:
                lidarr_logger.error(f"Failed to trigger ArtistSearch command for artist ID: {artist_id}.")

    # --- Album Mode ---
    elif hunt_missing_mode == 'album':
        lidarr_logger.info(f"Processing in 'album' mode. Selecting up to {hunt_missing_items} specific albums.")
        
        # Select albums to process
        albums_to_process = albums_to_consider
        if random_missing:
            lidarr_logger.debug(f"Randomly selecting albums.")
            random.shuffle(albums_to_process)
            
        albums_to_search = albums_to_process[:hunt_missing_items]
        album_ids_to_search = [album['id'] for album in albums_to_search]
        
        if not album_ids_to_search:
             lidarr_logger.info("No specific albums selected to search.")
             return False
        
        # Log more details about the selected albums
        album_details = [f"{album.get('title', 'Unknown')} by {album.get('artist', {}).get('artistName', 'Unknown Artist')} (ID: {album['id']})" for album in albums_to_search]
        lidarr_logger.info(f"Selected {len(album_ids_to_search)} specific albums to search:")
        for album_detail in album_details:
            lidarr_logger.info(f" - {album_detail}")

        # Optional: Refresh artists for selected albums? (Could be many API calls)
        # Let's skip artist refresh in album mode for now unless skip_artist_refresh is explicitly False.
        if not skip_artist_refresh:
             artist_ids_to_refresh = {album['artistId'] for album in albums_to_search if album.get('artistId')}
             lidarr_logger.info(f"Refreshing {len(artist_ids_to_refresh)} artists related to selected albums (skip_artist_refresh=False).")
             for artist_id in artist_ids_to_refresh:
                 if stop_check(): lidarr_logger.info("Stop requested during artist refresh in album mode."); break
                 lidarr_logger.debug(f"Attempting to refresh artist ID: {artist_id}")
                 refresh_command = lidarr_api.refresh_artist(api_url, api_key, api_timeout, artist_id)
                 if refresh_command and refresh_command.get('id'):
                     # Don't wait excessively long for each refresh here, maybe shorter timeout?
                     wait_for_command(api_url, api_key, api_timeout, refresh_command['id'], command_wait_delay, 10, f"RefreshArtist {artist_id} (Album Mode)", stop_check, log_success=False) # Don't spam logs
                 else:
                     lidarr_logger.warning(f"Failed to trigger RefreshArtist command for artist ID: {artist_id} in album mode.")
             if stop_check(): lidarr_logger.info("Stop requested after artist refresh in album mode."); return processed_any # Exit if stopped

        # Trigger Album Search for the selected batch
        lidarr_logger.debug(f"Attempting AlbumSearch for album IDs: {album_ids_to_search}")
        search_command = lidarr_api.search_albums(api_url, api_key, api_timeout, album_ids_to_search)

        if search_command and search_command.get('id'):
            if wait_for_command(
                api_url, api_key, api_timeout, search_command['id'],
                command_wait_delay, command_wait_attempts, f"AlbumSearch {len(album_ids_to_search)} albums", stop_check
            ):
                processed_in_this_run.update(album_ids_to_search)
                processed_any = True
                
                # Increment the hunted statistics for Lidarr
                increment_stat("lidarr", "hunted", len(album_ids_to_search))
                lidarr_logger.debug(f"Incremented lidarr hunted statistics by {len(album_ids_to_search)}")
                
                lidarr_logger.info(f"Successfully processed AlbumSearch for {len(album_ids_to_search)} albums.")
            else:
                lidarr_logger.warning(f"AlbumSearch command (ID: {search_command['id']}) did not complete successfully or timed out. Albums will not be marked as processed yet.")
        else:
            lidarr_logger.error(f"Failed to trigger AlbumSearch command for album IDs: {album_ids_to_search}.")

    # --- Update State ---
    if processed_in_this_run:
        updated_processed_ids = processed_album_ids.union(processed_in_this_run)
        save_processed_ids(PROCESSED_MISSING_FILE, list(updated_processed_ids))
        lidarr_logger.info(f"Saved {len(processed_in_this_run)} newly processed missing album IDs for Lidarr. Total processed: {len(updated_processed_ids)}.")
    elif processed_any: 
        lidarr_logger.info("Attempted missing content processing, but no new items were marked as successfully processed.")

    lidarr_logger.info("Finished missing content processing cycle for Lidarr.")
    return processed_any

def wait_for_command(
    api_url: str,
    api_key: str,
    api_timeout: int,
    command_id: int,
    delay: int,
    attempts: int,
    command_name: str,
    stop_check: Callable[[], bool],
    log_success: bool = True # Option to suppress success log spam
) -> bool:
    """Wait for a Lidarr command to complete, checking for stop requests."""
    lidarr_logger.debug(f"Waiting for Lidarr command '{command_name}' (ID: {command_id}) to complete...")
    start_time = time.monotonic()
    
    for attempt in range(attempts):
        if stop_check():
            lidarr_logger.info(f"Stop requested while waiting for command '{command_name}' (ID: {command_id}).")
            return False # Indicate command did not complete successfully due to stop

        status_data = lidarr_api.get_command_status(api_url, api_key, api_timeout, command_id)
        
        if status_data and isinstance(status_data, dict):
            status = status_data.get('status')
            state = status_data.get('state') # Lidarr v1 uses 'state' more often? Check API
            
            # Use 'state' if available, otherwise 'status'
            current_state = state if state else status 

            if current_state == 'completed':
                if log_success:
                     lidarr_logger.info(f"Lidarr command '{command_name}' (ID: {command_id}) completed successfully.")
                else:
                     lidarr_logger.debug(f"Lidarr command '{command_name}' (ID: {command_id}) completed successfully.")
                return True
            elif current_state in ['failed', 'aborted']:
                error_message = status_data.get('errorMessage') # Lidarr might have errorMessage
                if not error_message:
                     # Look in body or exception if available (adapt based on actual Lidarr responses)
                     body = status_data.get('body', {})
                     error_message = body.get('message', body.get('exception', f"Command {current_state}"))
                lidarr_logger.error(f"Lidarr command '{command_name}' (ID: {command_id}) {current_state}. Error: {error_message}")
                return False
            else: # queued, started, running, processing etc.
                elapsed_time = time.monotonic() - start_time
                lidarr_logger.debug(f"Lidarr command '{command_name}' (ID: {command_id}) state: {current_state}. Waiting {delay}s... (Attempt {attempt + 1}/{attempts}, Elapsed: {elapsed_time:.1f}s)")
        else:
            elapsed_time = time.monotonic() - start_time
            lidarr_logger.warning(f"Could not get status for Lidarr command '{command_name}' (ID: {command_id}). Retrying... (Attempt {attempt + 1}/{attempts}, Elapsed: {elapsed_time:.1f}s)")

        # Wait for the delay, checking stop_check frequently
        wait_start_time = time.monotonic()
        while time.monotonic() < wait_start_time + delay:
            if stop_check():
                lidarr_logger.info(f"Stop requested while waiting between checks for command '{command_name}' (ID: {command_id}).")
                return False
            # Sleep for 1 second or remaining time, whichever is smaller
            sleep_interval = min(1, (wait_start_time + delay) - time.monotonic())
            if sleep_interval > 0:
                 time.sleep(sleep_interval) 
            # Break if the delay time has passed to avoid infinite loop on clock skew
            if time.monotonic() >= wait_start_time + delay:
                 break

    elapsed_time = time.monotonic() - start_time
    lidarr_logger.error(f"Lidarr command '{command_name}' (ID: {command_id}) timed out after {attempts} attempts ({elapsed_time:.1f}s).")
    return False