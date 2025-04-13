#!/usr/bin/env python3
"""
Quality Upgrade Processing for Lidarr
Handles searching for tracks/albums that need quality upgrades in Lidarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from primary.utils.logger import get_logger
from primary.config import MONITORED_ONLY
from primary import settings_manager
from primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from primary.apps.lidarr.api import get_cutoff_unmet_albums, refresh_artist, album_search

# Get app-specific logger
logger = get_logger("lidarr")

def get_current_upgrade_limit():
    """Get the current HUNT_UPGRADE_TRACKS value directly from config"""
    return settings_manager.get_setting("huntarr", "hunt_upgrade_tracks", 0)

def process_cutoff_upgrades(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process tracks that need quality upgrades (cutoff unmet).
    
    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Reload settings to ensure the latest values are used
    from primary.config import refresh_settings
    refresh_settings("lidarr")

    # Get the current value directly at the start of processing
    HUNT_UPGRADE_TRACKS = get_current_upgrade_limit()
    RANDOM_UPGRADES = settings_manager.get_setting("advanced", "random_upgrades", True)
    SKIP_ARTIST_REFRESH = settings_manager.get_setting("advanced", "skip_artist_refresh", False)
    
    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("lidarr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if HUNT_UPGRADE_TRACKS is set to 0
    if HUNT_UPGRADE_TRACKS <= 0:
        logger.info("HUNT_UPGRADE_TRACKS is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get albums needing quality upgrades
    logger.info("Retrieving albums that need quality upgrades...")
    upgrade_albums = get_cutoff_unmet_albums()
    
    if not upgrade_albums:
        logger.info("No albums found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving albums
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade albums. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_albums)} albums that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    albums_processed = 0
    processing_done = False
    
    # Filter out already processed albums
    unprocessed_albums = [album for album in upgrade_albums if album.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_albums:
        logger.info("All upgrade albums have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_albums)} upgrade albums that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_UPGRADES:
        logger.info("Using random selection for quality upgrades (RANDOM_UPGRADES=true)")
        random.shuffle(unprocessed_albums)
    else:
        logger.info("Using sequential selection for quality upgrades (RANDOM_UPGRADES=false)")
        # Sort by title for consistent ordering
        unprocessed_albums.sort(key=lambda x: x.get("title", ""))
    
    # Check for restart signal before processing albums
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing albums. Aborting...")
        return False
    
    # Process up to HUNT_UPGRADE_TRACKS albums
    for album in unprocessed_albums:
        # Check for restart signal before each album
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during album processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = get_current_upgrade_limit()
        
        if albums_processed >= current_limit:
            logger.info(f"Reached HUNT_UPGRADE_TRACKS={current_limit} for this cycle.")
            break
        
        album_id = album.get("id")
        title = album.get("title", "Unknown Title")
        artist_id = album.get("artistId")
        artist_name = "Unknown Artist"
        
        # Look for artist name in the album
        if "artist" in album and isinstance(album["artist"], dict):
            artist_name = album["artist"].get("artistName", "Unknown Artist")
        elif "artist" in album and isinstance(album["artist"], str):
            artist_name = album["artist"]
        
        # Get quality information
        quality_info = ""
        if "quality" in album and album["quality"]:
            quality_name = album["quality"].get("quality", {}).get("name", "Unknown")
            quality_info = f" (Current quality: {quality_name})"
        
        logger.info(f"Processing quality upgrade for: \"{title}\" by {artist_name}{quality_info} (Album ID: {album_id})")
        
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
        logger.info(" - Searching for quality upgrade...")
        search_res = album_search([album_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, album_id)
            albums_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = get_current_upgrade_limit()
            logger.info(f"Processed {albums_processed}/{current_limit} upgrade albums this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for album ID {album_id}.")
            continue
    
    # Log final status
    current_limit = get_current_upgrade_limit()
    logger.info(f"Completed processing {albums_processed} upgrade albums for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done