#!/usr/bin/env python3
"""
Quality Upgrade Processing for Sonarr
Handles searching for episodes that need quality upgrades in Sonarr
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

# Get app-specific logger
logger = get_logger("sonarr")

def get_cutoff_unmet_episodes():
    """
    Get a list of episodes that need quality upgrades (cutoff unmet).
    
    Returns:
        A list of episode objects that need quality upgrades
    """
    from primary.apps.sonarr.api import arr_request
    
    # Get cutoff unmet episodes from Sonarr API
    params = "pageSize=1000"
    if MONITORED_ONLY:
        params += "&monitored=true"
    
    episodes = arr_request(f"wanted/cutoff?{params}")
    if not episodes or "records" not in episodes:
        return []
    
    return episodes.get("records", [])

def process_cutoff_upgrades(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process episodes that need quality upgrades (cutoff unmet).
    
    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Get the current value directly at the start of processing
    # Use settings_manager directly instead of get_current_upgrade_limit
    HUNT_UPGRADE_EPISODES = settings_manager.get_setting("sonarr", "hunt_upgrade_episodes", 0)
    RANDOM_UPGRADES = settings_manager.get_setting("sonarr", "random_upgrades", True)
    SKIP_SERIES_REFRESH = settings_manager.get_setting("sonarr", "skip_series_refresh", False)
    SKIP_FUTURE_EPISODES = settings_manager.get_setting("sonarr", "skip_future_episodes", True)
    MONITORED_ONLY = settings_manager.get_setting("sonarr", "monitored_only", True)

    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("sonarr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if HUNT_UPGRADE_EPISODES is set to 0
    if HUNT_UPGRADE_EPISODES <= 0:
        logger.info("HUNT_UPGRADE_EPISODES is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get episodes needing quality upgrades
    logger.info("Retrieving episodes that need quality upgrades...")
    upgrade_episodes = get_cutoff_unmet_episodes()
    
    if not upgrade_episodes:
        logger.info("No episodes found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving episodes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade episodes. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_episodes)} episodes that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    episodes_processed = 0
    processing_done = False
    
    # Filter out already processed episodes
    unprocessed_episodes = [ep for ep in upgrade_episodes if ep.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_episodes:
        logger.info("All upgrade episodes have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_episodes)} upgrade episodes that haven't been processed yet.")
    
    # Randomize if requested
    if RANDOM_UPGRADES:
        logger.info("Using random selection for quality upgrades (RANDOM_UPGRADES=true)")
        random.shuffle(unprocessed_episodes)
    else:
        logger.info("Using sequential selection for quality upgrades (RANDOM_UPGRADES=false)")
        # Sort by air date for consistent ordering
        unprocessed_episodes.sort(key=lambda x: x.get("airDateUtc", ""))
    
    # Check for restart signal before processing episodes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing episodes. Aborting...")
        return False
    
    # Process up to HUNT_UPGRADE_EPISODES episodes
    for episode in unprocessed_episodes:
        # Check for restart signal before each episode
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during episode processing. Aborting...")
            break
        
        # Check again for the current limit in case it was changed during processing
        # Use settings_manager directly instead of get_current_upgrade_limit
        current_limit = settings_manager.get_setting("sonarr", "hunt_upgrade_episodes", 0)
        
        if episodes_processed >= current_limit:
            logger.info(f"Reached HUNT_UPGRADE_EPISODES={current_limit} for this cycle.")
            break
        
        episode_id = episode.get("id")
        series_id = episode.get("seriesId")
        episode_num = episode.get("episodeNumber", "?")
        season_num = episode.get("seasonNumber", "?")
        series_title = episode.get("series", {}).get("title", "Unknown Series")
        episode_title = episode.get("title", "Unknown Title")
        
        # Get quality information
        quality_info = ""
        if "quality" in episode and episode["quality"]:
            quality_name = episode["quality"].get("quality", {}).get("name", "Unknown")
            quality_info = f" (Current quality: {quality_name})"
        
        # Get air date info
        air_date = "Unknown"
        if "airDateUtc" in episode:
            air_date_str = episode.get("airDateUtc", "")
            try:
                air_date = datetime.datetime.strptime(air_date_str.split('T')[0], "%Y-%m-%d").strftime("%b %d, %Y")
            except (ValueError, IndexError):
                air_date = air_date_str
        
        logger.info(f"Processing quality upgrade for: {series_title} - S{season_num:02d}E{episode_num:02d} - \"{episode_title}\"{quality_info} (Aired: {air_date}) (Episode ID: {episode_id})")
        
        # Refresh the series information if SKIP_SERIES_REFRESH is false
        if not SKIP_SERIES_REFRESH and series_id is not None:
            logger.info(" - Refreshing series information...")
            from primary.apps.sonarr.missing import refresh_series
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
        logger.info(" - Searching for quality upgrade...")
        from primary.apps.sonarr.missing import episode_search
        search_res = episode_search([episode_id])
        if search_res:
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, episode_id)
            episodes_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            # Use settings_manager directly instead of get_current_upgrade_limit
            current_limit = settings_manager.get_setting("sonarr", "hunt_upgrade_episodes", 0)
            logger.info(f"Processed {episodes_processed}/{current_limit} upgrade episodes this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for episode ID {episode_id}.")
            continue
    
    # Log final status
    # Use settings_manager directly instead of get_current_upgrade_limit
    current_limit = settings_manager.get_setting("sonarr", "hunt_upgrade_episodes", 0)
    logger.info(f"Completed processing {episodes_processed} upgrade episodes for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done