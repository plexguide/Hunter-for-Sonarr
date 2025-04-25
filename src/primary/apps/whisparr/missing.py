#!/usr/bin/env python3
"""
Missing Scenes Processing for Whisparr
Handles searching for missing scenes in Whisparr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional, Any, Set
from src.primary.utils.logger import get_logger, debug_log
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.whisparr.api import get_scenes_with_missing, refresh_scene, scene_search

# Get app-specific logger
logger = get_logger("whisparr")

def process_missing_scenes(
    app_settings: Dict[str, Any], 
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process scenes that are missing from the library.

    Args:
        app_settings: Dictionary containing settings for Whisparr.
        stop_check: Function that returns True if processing should stop.

    Returns:
        True if any processing was done, False otherwise
    """
    # Get settings from the passed dictionary
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 60)
    hunt_missing_scenes = app_settings.get("hunt_missing_scenes", 1)
    random_missing = app_settings.get("random_missing", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    command_wait_delay = app_settings.get("command_wait_delay", 1)
    command_wait_attempts = app_settings.get("command_wait_attempts", 600)

    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("whisparr", "processed_missing")

    logger.info("=== Checking for Missing Scenes ===")

    if not api_url or not api_key:
        logger.error("API URL or Key not configured in settings. Cannot process missing scenes.")
        return False

    # Skip if hunt_missing_scenes is set to 0
    if hunt_missing_scenes <= 0:
        logger.info("'hunt_missing_scenes' setting is 0 or less. Skipping missing scene processing.")
        return False

    # Check for stop signal
    if stop_check():
        logger.info("Stop requested before starting missing scenes. Aborting...")
        return False
    
    # Get missing scenes
    logger.info("Retrieving scenes with missing files...")
    missing_scenes = get_scenes_with_missing(api_url, api_key, api_timeout, monitored_only) 
    
    if missing_scenes is None: # API call failed
        logger.error("Failed to retrieve missing scenes from Whisparr API.")
        return False
        
    if not missing_scenes:
        logger.info("No missing scenes found.")
        return False
    
    # Check for stop signal after retrieving scenes
    if stop_check():
        logger.info("Stop requested after retrieving missing scenes. Aborting...")
        return False
    
    logger.info(f"Found {len(missing_scenes)} scenes with missing files.")
    
    # Filter out future releases if configured
    if skip_future_releases:
        now = datetime.datetime.now(datetime.timezone.utc)
        original_count = len(missing_scenes)
        # Whisparr scene object has 'airDateUtc' for release dates
        missing_scenes = [
            scene for scene in missing_scenes
            if not scene.get('airDateUtc') or (
                scene.get('airDateUtc') and 
                datetime.datetime.fromisoformat(scene['airDateUtc'].replace('Z', '+00:00')) < now
            )
        ]
        skipped_count = original_count - len(missing_scenes)
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} future scene releases based on air date.")

    if not missing_scenes:
        logger.info("No missing scenes left to process after filtering future releases.")
        return False
        
    processed_missing_ids: Set[int] = load_processed_ids(PROCESSED_MISSING_FILE)
    scenes_processed = 0
    processing_done = False
    
    # Filter out already processed scenes
    unprocessed_scenes = [scene for scene in missing_scenes if scene.get("id") not in processed_missing_ids]
    
    if not unprocessed_scenes:
        logger.info("All available missing scenes have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_scenes)} missing scenes that haven't been processed yet.")
    
    # Select scenes to search based on configuration
    if random_missing:
        logger.info(f"Randomly selecting up to {hunt_missing_scenes} missing scenes.")
        scenes_to_search = random.sample(unprocessed_scenes, min(len(unprocessed_scenes), hunt_missing_scenes))
    else:
        logger.info(f"Selecting the first {hunt_missing_scenes} missing scenes (sorted by title).")
        # Sort by sceneName for consistent ordering if not random
        unprocessed_scenes.sort(key=lambda x: x.get("sceneName", ""))
        scenes_to_search = unprocessed_scenes[:hunt_missing_scenes]
    
    logger.info(f"Selected {len(scenes_to_search)} missing scenes to search.")

    processed_in_this_run = set()
    # Process selected scenes
    for scene in scenes_to_search:
        # Check for stop signal before each scene
        if stop_check():
            logger.info("Stop requested during scene processing. Aborting...")
            break
        
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_missing_scenes", 1)
        if scenes_processed >= current_limit:
             logger.info(f"Reached HUNT_MISSING_SCENES limit ({current_limit}) for this cycle.")
             break

        scene_id = scene.get("id")
        title = scene.get("sceneName", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        
        logger.info(f"Processing missing scene: \"{title}\" - {season_episode} (Scene ID: {scene_id})")
        
        # Refresh the scene information if not skipped
        refresh_command_id = None
        if not skip_scene_refresh:
            logger.info(" - Refreshing scene information...")
            refresh_command_id = refresh_scene(api_url, api_key, api_timeout, scene_id)
            if refresh_command_id:
                logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                time.sleep(5) # Basic wait
            else:
                logger.warning(f"Failed to trigger refresh command for scene ID: {scene_id}. Proceeding without refresh.")
        else:
            logger.info(" - Skipping scene refresh (skip_scene_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the scene
        logger.info(" - Searching for missing scene...")
        search_command_id = scene_search(api_url, api_key, api_timeout, [scene_id])
        if search_command_id:
            logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            save_processed_id(PROCESSED_MISSING_FILE, scene_id)
            processed_in_this_run.add(scene_id)
            scenes_processed += 1
            processing_done = True

            # Log progress
            current_limit = app_settings.get("hunt_missing_scenes", 1)
            logger.info(f"Processed {scenes_processed}/{current_limit} missing scenes this cycle.")
        else:
            logger.warning(f"Failed to trigger search command for scene ID {scene_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if processed_in_this_run:
        logger.info(f"Completed processing {len(processed_in_this_run)} missing scenes for this cycle.")
    else:
        logger.info("No new missing scenes were processed in this run.")
        
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done