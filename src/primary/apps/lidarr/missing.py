#!/usr/bin/env python3
"""
Lidarr missing content processing module for Huntarr
Handles missing albums or artists based on configuration.
"""

import time
import random
import datetime
import os
import json
from typing import Dict, Any, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.stats_manager import increment_stat
from src.primary.stateful_manager import is_processed, add_processed_id
from src.primary.utils.history_utils import log_processed_media
from src.primary.state import get_state_file_path, check_state_reset
import json
import os

# Get the logger for the Lidarr module
lidarr_logger = get_logger(__name__) # Use __name__ for correct logger hierarchy


def process_missing_albums(
    app_settings: Dict[str, Any],      # Combined settings dictionary
    stop_check: Callable[[], bool] = None      # Function to check for stop signal
) -> bool:
    """
    Processes missing albums for a specific Lidarr instance based on settings.

    Args:
        app_settings (dict): Dictionary containing combined instance and general settings.
        stop_check (Callable[[], bool]): Function to check if shutdown is requested.

    Returns:
        bool: True if any items were processed, False otherwise.
    """
    
    # Copy instance-specific information
    instance_name = app_settings.get("instance_name", "Default")
    api_url = app_settings.get("api_url", "").strip()
    api_key = app_settings.get("api_key", "").strip()
    api_timeout = app_settings.get("api_timeout", 90)
    
    # Extract settings
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", False)
    hunt_missing_items = app_settings.get("hunt_missing_items", 0)
    hunt_missing_mode = app_settings.get("hunt_missing_mode", "album")
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    
    # Early exit for disabled features
    if not api_url or not api_key:
        lidarr_logger.warning(f"Missing API URL or API key, skipping missing processing for {instance_name}")
        return False
    
    if hunt_missing_items <= 0:
        lidarr_logger.debug(f"Hunting for missing items is disabled (hunt_missing_items={hunt_missing_items}) for {instance_name}")
        return False
    
    # Make sure any requested stop function is executable
    stop_check = stop_check if callable(stop_check) else lambda: False
    
    lidarr_logger.info(f"Looking for missing albums for {instance_name}")
    lidarr_logger.debug(f"Processing up to {hunt_missing_items} missing items in {hunt_missing_mode} mode")
    
    # Reset state files if enough time has passed
    check_state_reset("lidarr")
    
    # Initialize processed counter and tracking containers
    processed_count = 0
    processed_any = False
    processed_artists_or_albums = set()
    total_items_to_process = hunt_missing_items

    try:
        # Fetch all missing albums first
        lidarr_logger.info(f"Fetching all missing albums for {instance_name}...")
        missing_items = lidarr_api.get_missing_albums(
            api_url,
            api_key,
            monitored_only=monitored_only,
            api_timeout=api_timeout
        )

        if missing_items is None: # API call failed or returned None
            lidarr_logger.error(f"Failed to get missing items from Lidarr API for {instance_name}.")
            return False

        if not missing_items:
            lidarr_logger.info(f"No missing albums found for {instance_name} after initial fetch and filtering.")
            return False

        lidarr_logger.info(f"Found {len(missing_items)} potentially missing albums for {instance_name} after initial fetch.")

        # --- Filter Future Releases --- #
        original_count = len(missing_items)
        if skip_future_releases:
            now = datetime.datetime.now(datetime.timezone.utc)
            valid_missing_items = []
            skipped_count = 0
            for item in missing_items:
                release_date_str = item.get('releaseDate')
                if release_date_str:
                    try:
                        # Lidarr dates often include 'Z' for UTC
                        release_date = datetime.datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
                        if release_date <= now:
                            valid_missing_items.append(item)
                        else:
                            # lidarr_logger.debug(f"Skipping future album ID {item.get('id')} ('{item.get('title')}') release: {release_date_str}")
                            skipped_count += 1
                    except ValueError as e:
                        lidarr_logger.warning(f"Could not parse release date '{release_date_str}' for album ID {item.get('id')}. Error: {e}. Including it.")
                        valid_missing_items.append(item) # Keep if date is invalid
                else:
                    valid_missing_items.append(item) # Keep if no release date
            
            missing_items = valid_missing_items # Replace with filtered list
            if skipped_count > 0:
                lidarr_logger.info(f"Skipped {skipped_count} future albums based on release date. {len(missing_items)} remaining.")
        else:
             lidarr_logger.debug("Skipping future release filtering as 'skip_future_releases' is False.")
        
        # Check if any items remain after filtering
        if not missing_items:
            lidarr_logger.info(f"No missing albums left after filtering future releases for {instance_name}.")
            return False

        # Process based on mode
        lidarr_logger.info(f"Processing missing items in '{hunt_missing_mode}' mode.")

        target_entities = []
        search_entity_type = "album" # Default to album

        if hunt_missing_mode == "artist":
            search_entity_type = "artist"
            # Group by artist ID
            items_by_artist = {}
            for item in missing_items: # Use the potentially filtered missing_items list
                artist_id = item.get('artistId')
                lidarr_logger.debug(f"Missing album item: {item.get('title')} by artistId: {artist_id}")
                if artist_id:
                    if artist_id not in items_by_artist:
                        items_by_artist[artist_id] = []
                    items_by_artist[artist_id].append(item)
            
            # In artist mode, map from artists to their albums
            # First, get all artist IDs
            target_entities = list(items_by_artist.keys())
            
            # Filter out already processed artists
            lidarr_logger.info(f"Found {len(target_entities)} artists with missing albums before filtering")
            unprocessed_entities = [eid for eid in target_entities 
                                   if not is_processed("lidarr", instance_name, str(eid))]
            
            lidarr_logger.info(f"Found {len(unprocessed_entities)} unprocessed artists out of {len(target_entities)} total")
        else:
            # In album mode, directly track album IDs
            target_entities = [item['id'] for item in missing_items]
            
            # Filter out processed albums
            lidarr_logger.info(f"Found {len(target_entities)} missing albums before filtering")
            unprocessed_entities = [eid for eid in target_entities 
                                   if not is_processed("lidarr", instance_name, str(eid))]
            
            lidarr_logger.info(f"Found {len(unprocessed_entities)} unprocessed albums out of {len(target_entities)} total")
        
        if not unprocessed_entities:
            lidarr_logger.info(f"No unprocessed {search_entity_type}s found for {instance_name}. All available {search_entity_type}s have been processed.")
            return False
            
        # Select entities to search
        if not unprocessed_entities:
            lidarr_logger.info(f"No {search_entity_type}s found to process after grouping/filtering.")
            return False

        entities_to_search_ids = random.sample(unprocessed_entities, min(len(unprocessed_entities), total_items_to_process))
        lidarr_logger.info(f"Randomly selected {len(entities_to_search_ids)} {search_entity_type}s to search.")
        lidarr_logger.debug(f"Unprocessed entities: {unprocessed_entities}")
        lidarr_logger.debug(f"Entities to search: {entities_to_search_ids}")

        # --- Trigger Search (Artist or Album) ---
        if hunt_missing_mode == "artist":
            lidarr_logger.info(f"Artist-based missing mode selected")
            lidarr_logger.info(f"Found {len(entities_to_search_ids)} unprocessed artists to search.")
            
            # Prepare a list for artist details log
            artist_details_log = []
            
            lidarr_logger.info(f"Triggering Artist Search for {len(entities_to_search_ids)} artists on {instance_name}...")
            for i, artist_id in enumerate(entities_to_search_ids):
                if stop_check(): # Use the new stop_check function
                    lidarr_logger.warning("Shutdown requested during artist search trigger.")
                    break

                # Get artist name from the first album associated with this artist ID
                artist_name = f"Artist ID {artist_id}" # Default if name not found
                if artist_id in items_by_artist and items_by_artist[artist_id]:
                    # Access nested structure safely
                    first_album = items_by_artist[artist_id][0]
                    artist_info = first_album.get('artist')
                    if artist_info and isinstance(artist_info, dict):
                         artist_name = artist_info.get('artistName', artist_name)
                
                # Add to detailed log list
                artist_details_log.append(f"{i+1}. {artist_name} (ID: {artist_id})")

                lidarr_logger.info(f"Triggering Artist Search for '{artist_name}' (ID: {artist_id}) on instance {instance_name}")
                
                # Mark the artist as processed right away - BEFORE triggering the search
                success = add_processed_id("lidarr", instance_name, str(artist_id))
                lidarr_logger.debug(f"Added artist ID {artist_id} to processed list for {instance_name}, success: {success}")
                
                # Trigger the search AFTER marking as processed
                lidarr_api.search_artist(api_url, api_key, api_timeout, artist_id)
                lidarr_logger.info(f"Successfully triggered search for artist '{artist_name}' (ID: {artist_id})")
                
                # Also mark all albums from this artist as processed
                if artist_id in items_by_artist:
                    for album in items_by_artist[artist_id]:
                        album_id = album.get('id')
                        if album_id:
                            album_success = add_processed_id("lidarr", instance_name, str(album_id))
                            lidarr_logger.debug(f"Added album ID {album_id} to processed list for {instance_name}, success: {album_success}")
                
                # Log to history system
                log_processed_media("lidarr", f"{artist_name}", artist_id, instance_name, "missing")
                lidarr_logger.debug(f"Logged history entry for artist: {artist_name}")
                
                time.sleep(0.1) # Small delay between triggers
        else: # Album mode
            album_ids_to_search = list(entities_to_search_ids)
            if stop_check(): # Use the new stop_check function
                lidarr_logger.warning("Shutdown requested before album search trigger.")
                return False

            # Prepare descriptive list for logging
            album_details_log = []
            # Create a dict for quick lookup based on album ID
            missing_items_dict = {item['id']: item for item in missing_items if 'id' in item}
            for album_id in album_ids_to_search:
                album_info = missing_items_dict.get(album_id)
                if album_info:
                    # Safely get title and artist name, provide defaults
                    title = album_info.get('title', f'Album ID {album_id}')
                    artist_name = album_info.get('artist', {}).get('artistName', 'Unknown Artist')
                    album_details_log.append(f"{len(album_details_log) + 1}. {artist_name} - {title} (ID: {album_id})")
                else:
                    # Fallback if album ID wasn't found in the fetched missing items (should be rare)
                    album_details_log.append(f"{len(album_details_log) + 1}. Album ID {album_id} (Details not found)")

            # Log each album on a new line for better readability
            lidarr_logger.info(f"Albums selected for processing in this cycle:")
            for album_detail in album_details_log:
                lidarr_logger.info(f" {album_detail}")

            # Mark the albums as processed BEFORE triggering the search
            for album_id in album_ids_to_search:
                success = add_processed_id("lidarr", instance_name, str(album_id))
                lidarr_logger.debug(f"Added album ID {album_id} to processed list for {instance_name}, success: {success}")
            
            # Now trigger the search
            command_id = lidarr_api.search_albums(api_url, api_key, api_timeout, album_ids_to_search)
            if command_id:
                # Log after successful search
                lidarr_logger.debug(f"Album search command triggered with ID: {command_id} for albums: [{', '.join(album_details_log)}]")
                increment_stat("lidarr", "hunted") # Changed from "missing" to "hunted"
                processed_count += len(album_ids_to_search) # Count albums searched
                processed_artists_or_albums.update(album_ids_to_search)
                
                # Log to history system
                for album_id in album_ids_to_search:
                    album_info = missing_items_dict.get(album_id)
                    if album_info:
                        # Get title and artist name for the history entry
                        title = album_info.get('title', f'Album ID {album_id}')
                        artist_name = album_info.get('artist', {}).get('artistName', 'Unknown Artist')
                        media_name = f"{artist_name} - {title}"
                        log_processed_media("lidarr", media_name, album_id, instance_name, "missing")
                        lidarr_logger.debug(f"Logged history entry for album: {media_name}")
                
                time.sleep(command_wait_delay) # Basic delay after the single command
            else:
                lidarr_logger.warning(f"Failed to trigger album search for IDs {album_ids_to_search} on {instance_name}.")

    except Exception as e:
        lidarr_logger.error(f"An error occurred during missing album processing for {instance_name}: {e}", exc_info=True)
        return False

    lidarr_logger.info(f"Missing album processing finished for {instance_name}. Processed {processed_count} items/searches ({len(processed_artists_or_albums)} unique {search_entity_type}s).")
    return processed_count > 0