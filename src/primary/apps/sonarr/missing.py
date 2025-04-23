#!/usr/bin/env python3
"""
Missing Episodes Processing for Sonarr
Handles searching for missing episodes in Sonarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from src.primary.utils.logger import get_logger
from src.primary.config import MONITORED_ONLY
from src.primary import settings_manager
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path

# Get app-specific logger
logger = get_logger("sonarr")

def get_missing_episodes():
    """
    Get a list of missing episodes from Sonarr.
    
    Returns:
        A list of episode objects that are missing
    """
    from primary.apps.sonarr.api import arr_request
    
    # Get missing episodes from Sonarr API
    params = "pageSize=1000"
    if MONITORED_ONLY:
        params += "&monitored=true"
    
    episodes = arr_request(f"wanted/missing?{params}")
    if not episodes or "records" not in episodes:
        return []
    
    return episodes.get("records", [])

def episode_search(episode_ids: List[int]) -> bool:
    """
    Trigger a search for one or more episodes.
    
    Args:
        episode_ids: A list of episode IDs to search for
        
    Returns:
        True if the search command was successful, False otherwise
    """
    from primary.apps.sonarr.api import arr_request
    
    endpoint = "command"
    data = {
        "name": "EpisodeSearch",
        "episodeIds": episode_ids
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Triggered search for episode IDs: {episode_ids}")
        return True
    return False

def refresh_series(series_id: int) -> bool:
    """
    Refresh a series in Sonarr.
    
    Args:
        series_id: The ID of the series to refresh
        
    Returns:
        True if the refresh was successful, False otherwise
    """
    from primary.apps.sonarr.api import arr_request
    
    endpoint = "command"
    data = {
        "name": "RefreshSeries",
        "seriesId": series_id
    }
    
    response = arr_request(endpoint, method="POST", data=data)
    if response:
        logger.debug(f"Refreshed series ID {series_id}")
        return True
    return False

def process_missing_episodes(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process episodes that are missing from the library.
    
    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Removed refresh_settings call
    
    # Get the current value directly at the start of processing
    HUNT_MISSING_EPISODES = settings_manager.get_setting("sonarr", "hunt_missing_shows", 3)
    RANDOM_MISSING = settings_manager.get_setting("sonarr", "random_missing", True)
    SKIP_SERIES_REFRESH = settings_manager.get_setting("sonarr", "skip_series_refresh", False)
    
    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("sonarr", "processed_missing")
    
    logger.info("=== Checking for Missing Episodes ===")
    
    # Skip if HUNT_MISSING_EPISODES is set to 0
    if HUNT_MISSING_EPISODES <= 0:
        logger.info("HUNT_MISSING_EPISODES is set to 0, skipping missing episodes")
        return False
    
    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting missing episodes. Aborting...")
        return False
    
    # Get missing episodes
    logger.info("Retrieving episodes with missing files...")
    missing_episodes = get_missing_episodes()
    
    if not missing_episodes:
        logger.info("No missing episodes found.")
        return False
    
    # Check for restart signal after retrieving episodes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving missing episodes. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_episodes)} episodes with missing files.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    episodes_processed = 0
    processing_done = False
    
    # Filter out already processed episodes
    unprocessed_episodes = [ep for ep in missing_episodes if ep.get("id") not in processed_missing_ids]
    
    if not unprocessed_episodes:
        logger.info("All missing episodes have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_episodes)} missing episodes that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_MISSING:
        logger.info("Using random selection for missing episodes (RANDOM_MISSING=true)")
        random.shuffle(unprocessed_episodes)
    else:
        logger.info("Using sequential selection for missing episodes (RANDOM_MISSING=false)")
        # Sort by air date for consistent ordering
        unprocessed_episodes.sort(key=lambda x: x.get("airDateUtc", ""))
    
    # Check for restart signal before processing episodes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing episodes. Aborting...")
        return False
    
    # Process up to HUNT_MISSING_EPISODES episodes
    for episode in unprocessed_episodes:
        # Check for restart signal before each episode
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during episode processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        current_limit = settings_manager.get_setting("sonarr", "hunt_missing_shows", 3)
        
        if episodes_processed >= current_limit:
            logger.info(f"Reached HUNT_MISSING_SHOWS={current_limit} for this cycle.")
            break
        
        episode_id = episode.get("id")
        series_id = episode.get("seriesId")
        episode_num = episode.get("episodeNumber", "?")
        season_num = episode.get("seasonNumber", "?")
        
        # Fix series title extraction - the series data might be nested differently than expected
        series_title = "Unknown Series"
        if "series" in episode and isinstance(episode["series"], dict) and "title" in episode["series"]:
            series_title = episode["series"]["title"]
        # If we didn't get the title and have series_id, try to fetch it directly
        elif series_id is not None:
            from primary.apps.sonarr.api import arr_request
            series_data = arr_request(f"series/{series_id}", method="GET")
            if series_data and "title" in series_data:
                series_title = series_data["title"]
                
        episode_title = episode.get("title", "Unknown Title")
        
        # Get air date info
        air_date = "Unknown"
        if "airDateUtc" in episode:
            air_date_str = episode.get("airDateUtc", "")
            try:
                air_date = datetime.datetime.strptime(air_date_str.split('T')[0], "%Y-%m-%d").strftime("%b %d, %Y")
            except (ValueError, IndexError):
                air_date = air_date_str
        
        logger.info(f"Processing missing episode: {series_title} - S{season_num:02d}E{episode_num:02d} - \"{episode_title}\" (Aired: {air_date}) (Episode ID: {episode_id})")
        
        # Refresh the series information if SKIP_SERIES_REFRESH is false
        if not SKIP_SERIES_REFRESH and series_id is not None:
            logger.info(" - Refreshing series information...")
            refresh_res = refresh_series(series_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this episode.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Sonarr to process
            time.sleep(2)
        else:
            reason = "SKIP_SERIES_REFRESH=true" if SKIP_SERIES_REFRESH else "series_id is None"
            logger.info(f" - Skipping series refresh ({reason})")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {series_title} - S{season_num:02d}E{episode_num:02d}. Aborting...")
            break
        
        # Search for the episode
        logger.info(" - Searching for missing episode...")
        search_res = episode_search([episode_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_MISSING_FILE, episode_id)
            episodes_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = settings_manager.get_setting("sonarr", "hunt_missing_shows", 3)
            logger.info(f"Processed {episodes_processed}/{current_limit} missing episodes this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for episode ID {episode_id}.")
            continue
    
    # Log final status
    current_limit = settings_manager.get_setting("sonarr", "hunt_missing_shows", 3)
    logger.info(f"Completed processing {episodes_processed} missing episodes for this cycle.")
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done