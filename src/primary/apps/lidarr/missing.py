#!/usr/bin/env python3
"""
Missing Albums Processing for Lidarr
Handles searching for missing albums in Lidarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from primary.utils.logger import get_logger, debug_log
from primary.config import MONITORED_ONLY
from primary import settings_manager
from primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from primary.apps.lidarr.api import get_albums_with_missing_tracks, refresh_artist, album_search

# Get app-specific logger
logger = get_logger("lidarr")

def process_missing_albums(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process albums that are missing from the library.

    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle

    Returns:
        True if any processing was done, False otherwise
    """
    # Reload settings to ensure the latest values are used
    from primary.config import refresh_settings
    refresh_settings("lidarr")

    # Get the current value directly at the start of processing
    HUNT_MISSING_ALBUMS = settings_manager.get_setting("huntarr", "hunt_missing_albums", 1)
    RANDOM_MISSING = settings_manager.get_setting("advanced", "random_missing", True)
    SKIP_ARTIST_REFRESH = settings_manager.get_setting("advanced", "skip_artist_refresh", False)
    
    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("lidarr", "processed_missing")

    logger.info("=== Checking for Missing Albums ===")

    # Skip if HUNT_MISSING_ALBUMS is set to 0
    if HUNT_MISSING_ALBUMS <= 0:
        logger.info("HUNT_MISSING_ALBUMS is set to 0, skipping missing albums")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting missing albums. Aborting...")
        return False
    
    # Get missing albums
    logger.info("Retrieving albums with missing tracks...")
    missing_albums = get_albums_with_missing_tracks()
    
    if not missing_albums:
        logger.info("No missing albums found.")
        return False
    
    # Check for restart signal after retrieving albums
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving missing albums. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_albums)} albums with missing tracks.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    albums_processed = 0
    processing_done = False
    
    # Filter out already processed albums
    unprocessed_albums = [album for album in missing_albums if album.get("id") not in processed_missing_ids]
    
    if not unprocessed_albums:
        logger.info("All missing albums have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_albums)} missing albums that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_MISSING:
        logger.info("Using random selection for missing albums (RANDOM_MISSING=true)")
        random.shuffle(unprocessed_albums)
    else:
        logger.info("Using sequential selection for missing albums (RANDOM_MISSING=false)")
        # Sort by title for consistent ordering
        unprocessed_albums.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing albums
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing albums. Aborting...")
        return False
    
    # Process up to HUNT_MISSING_ALBUMS albums
    for album in unprocessed_albums:
        # Check for restart signal before each album
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during album processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = settings_manager.get_setting("huntarr", "hunt_missing_albums", 1)
        
        if albums_processed >= current_limit:
            logger.info(f"Reached HUNT_MISSING_ALBUMS={current_limit} for this cycle.")
            break
        
        album_id = album.get("id")
        title = album.get("title", "Unknown Title")
        artist_id = album.get("artistId")
        artist_name = "Unknown Artist"
        
        # Look for artist name in the album
        if "artist" in album and isinstance(album["artist"], dict):
            artist_name = album["artist"].get("artistName", "Unknown Artist")
        
        album_type = album.get("albumType", "Unknown Type")
        release_date = album.get("releaseDate", "Unknown Release Date")
        
        logger.info(f"Processing missing album: \"{title}\" by {artist_name} ({album_type}, {release_date}) (Album ID: {album_id})")
        
        # Refresh the artist information if SKIP_ARTIST_REFRESH is false
        if not SKIP_ARTIST_REFRESH and artist_id is not None:
            logger.info(" - Refreshing artist information...")
            refresh_res = refresh_artist(artist_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this album.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Lidarr to process
            time.sleep(2)
        else:
            reason = "SKIP_ARTIST_REFRESH=true" if SKIP_ARTIST_REFRESH else "artist_id is None"
            logger.info(f" - Skipping artist refresh ({reason})")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {title}. Aborting...")
            break
        
        # Search for the album
        logger.info(" - Searching for missing album...")
        search_res = album_search([album_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_MISSING_FILE, album_id)
            albums_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = settings_manager.get_setting("huntarr", "hunt_missing_albums", 1)
            logger.info(f"Processed {albums_processed}/{current_limit} missing albums this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for album ID {album_id}.")
            continue
    
    # Log final status
    current_limit = settings_manager.get_setting("huntarr", "hunt_missing_albums", 1)
    logger.info(f"Completed processing {albums_processed} missing albums for this cycle.")
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done