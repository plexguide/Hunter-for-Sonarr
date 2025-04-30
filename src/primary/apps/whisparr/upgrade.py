#!/usr/bin/env python3
"""
Quality Upgrade Processing for Whisparr
Handles searching for scenes that need quality upgrades in Whisparr

Supports both v2 (legacy) and v3 (Eros) API versions
"""

import time
import random
import datetime
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.whisparr import api as whisparr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
whisparr_logger = get_logger("whisparr")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Whisparr based on settings.
    
    Args:
        app_settings: Dictionary containing all settings for Whisparr
        stop_check: A function that returns True if the process should stop
        
    Returns:
        True if any scenes were processed for upgrades, False otherwise.
    """
    whisparr_logger.info("Starting quality cutoff upgrades processing cycle for Whisparr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    
    # Use the new hunt_upgrade_items parameter name, falling back to hunt_upgrade_scenes for backwards compatibility
    hunt_upgrade_items = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 0))
    
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  
    
    # Get the API version to use (v2 or v3)
    api_version = app_settings.get("whisparr_version", "v3")
    whisparr_logger.info(f"Using Whisparr API version: {api_version}")

    # Skip if hunt_upgrade_items is set to 0
    if hunt_upgrade_items <= 0:
        whisparr_logger.info("'hunt_upgrade_items' setting is 0 or less. Skipping cutoff upgrade processing.")
        return False

    # Check for stop signal
    if stop_check():
        whisparr_logger.info("Stop requested before starting cutoff upgrades. Aborting...")
        return False
    
    # Get cutoff unmet scenes
    whisparr_logger.info(f"Retrieving scenes that need quality upgrades using API v{api_version}...")
    cutoff_unmet_scenes = whisparr_api.get_cutoff_unmet_scenes(api_url, api_key, api_timeout, monitored_only, api_version) 
    
    if cutoff_unmet_scenes is None: # API call failed
        whisparr_logger.error("Failed to retrieve cutoff unmet scenes from Whisparr API.")
        return False
        
    if not cutoff_unmet_scenes:
        whisparr_logger.info("No scenes found that need quality upgrades.")
        return False
    
    # Check for stop signal after retrieving scenes
    if stop_check():
        whisparr_logger.info("Stop requested after retrieving cutoff unmet scenes. Aborting...")
        return False
    
    whisparr_logger.info(f"Found {len(cutoff_unmet_scenes)} scenes that need quality upgrades.")
    
    scenes_processed = 0
    processing_done = False
    
    # Select scenes to search based on configuration
    if random_upgrades:
        whisparr_logger.info(f"Randomly selecting up to {hunt_upgrade_items} scenes for quality upgrade.")
        scenes_to_search = random.sample(cutoff_unmet_scenes, min(len(cutoff_unmet_scenes), hunt_upgrade_items))
    else:
        whisparr_logger.info(f"Selecting the first {hunt_upgrade_items} scenes for quality upgrade (sorted by title).")
        # Sort by title for consistent ordering if not random
        cutoff_unmet_scenes.sort(key=lambda x: x.get("title", ""))
        scenes_to_search = cutoff_unmet_scenes[:hunt_upgrade_items]
    
    whisparr_logger.info(f"Selected {len(scenes_to_search)} scenes for quality upgrades.")

    # Process selected scenes
    for scene in scenes_to_search:
        # Check for stop signal before each scene
        if stop_check():
            whisparr_logger.info("Stop requested during scene processing. Aborting...")
            break
        
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
        if scenes_processed >= current_limit:
            whisparr_logger.info(f"Reached HUNT_UPGRADE_ITEMS limit ({current_limit}) for this cycle.")
            break

        scene_id = scene.get("id")
        title = scene.get("title", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        
        whisparr_logger.info(f"Processing scene for quality upgrade: \"{title}\" - {season_episode} (Scene ID: {scene_id})")
        
        # Refresh the scene information if not skipped
        refresh_command_id = None
        if not skip_scene_refresh:
            whisparr_logger.info(" - Refreshing scene information...")
            refresh_command_id = whisparr_api.refresh_scene(api_url, api_key, api_timeout, scene_id, api_version)
            if refresh_command_id:
                whisparr_logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                time.sleep(5) # Basic wait
            else:
                whisparr_logger.warning(f"Failed to trigger refresh command for scene ID: {scene_id}. Proceeding without refresh.")
        else:
            whisparr_logger.info(" - Skipping scene refresh (skip_scene_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            whisparr_logger.info(f"Stop requested before searching for upgrade of {title}. Aborting...")
            break
        
        # Search for the scene
        whisparr_logger.info(" - Searching for quality upgrade...")
        search_command_id = whisparr_api.scene_search(api_url, api_key, api_timeout, [scene_id], api_version)
        if search_command_id:
            whisparr_logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            scenes_processed += 1
            processing_done = True
            
            # Increment the upgraded statistics for Whisparr
            increment_stat("whisparr", "upgraded", 1)
            whisparr_logger.debug(f"Incremented whisparr upgraded statistics by 1")

            # Log progress
            current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
            whisparr_logger.info(f"Processed {scenes_processed}/{current_limit} scenes for quality upgrades this cycle.")
        else:
            whisparr_logger.warning(f"Failed to trigger search command for scene ID {scene_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if scenes_processed > 0:
        whisparr_logger.info(f"Completed processing {scenes_processed} scenes for quality upgrades in this cycle.")
    else:
        whisparr_logger.info("No scenes were processed for quality upgrades in this run.")
        
    return processing_done