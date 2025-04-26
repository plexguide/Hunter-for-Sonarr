#!/usr/bin/env python3
"""
Missing Scenes Processing for Whisparr
Handles searching for missing scenes in Whisparr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path, truncate_processed_list
from src.primary.apps.whisparr import api as whisparr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
whisparr_logger = get_logger("whisparr")

# State file for processed missing scenes
PROCESSED_MISSING_FILE = get_state_file_path("whisparr", "processed_missing")

def process_missing_scenes(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing scenes in Whisparr based on provided settings.
    
    Args:
        app_settings: Dictionary containing all settings for Whisparr
        stop_check: A function that returns True if the process should stop
    
    Returns:
        True if any scenes were processed, False otherwise.
    """
    whisparr_logger.info("Starting missing scenes processing cycle for Whisparr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_scenes = app_settings.get("hunt_missing_scenes", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  # Add this line to get the stateful reset interval

    # Skip if hunt_missing_scenes is set to 0
    if hunt_missing_scenes <= 0:
        whisparr_logger.info("'hunt_missing_scenes' setting is 0 or less. Skipping missing scene processing.")
        return False

    # Check for stop signal
    if stop_check():
        whisparr_logger.info("Stop requested before starting missing scenes. Aborting...")
        return False
    
    # Get missing scenes
    whisparr_logger.info("Retrieving scenes with missing files...")
    missing_scenes = whisparr_api.get_scenes_with_missing(api_url, api_key, api_timeout, monitored_only) 
    
    if missing_scenes is None: # API call failed
        whisparr_logger.error("Failed to retrieve missing scenes from Whisparr API.")
        return False
        
    if not missing_scenes:
        whisparr_logger.info("No missing scenes found.")
        return False
    
    # Check for stop signal after retrieving scenes
    if stop_check():
        whisparr_logger.info("Stop requested after retrieving missing scenes. Aborting...")
        return False
    
    whisparr_logger.info(f"Found {len(missing_scenes)} scenes with missing files.")
    
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
            whisparr_logger.info(f"Skipped {skipped_count} future scene releases based on air date.")

    if not missing_scenes:
        whisparr_logger.info("No missing scenes left to process after filtering future releases.")
        return False
        
    processed_missing_ids: Set[int] = load_processed_ids(PROCESSED_MISSING_FILE)
    scenes_processed = 0
    processing_done = False
    
    # Filter out already processed scenes
    unprocessed_scenes = [scene for scene in missing_scenes if scene.get("id") not in processed_missing_ids]
    
    if not unprocessed_scenes:
        whisparr_logger.info("All available missing scenes have already been processed. Skipping.")
        return False
    
    whisparr_logger.info(f"Found {len(unprocessed_scenes)} missing scenes that haven't been processed yet.")
    
    # Select scenes to search based on configuration
    if random_missing:
        whisparr_logger.info(f"Randomly selecting up to {hunt_missing_scenes} missing scenes.")
        scenes_to_search = random.sample(unprocessed_scenes, min(len(unprocessed_scenes), hunt_missing_scenes))
    else:
        whisparr_logger.info(f"Selecting the first {hunt_missing_scenes} missing scenes (sorted by title).")
        # Sort by title for consistent ordering if not random
        unprocessed_scenes.sort(key=lambda x: x.get("title", ""))
        scenes_to_search = unprocessed_scenes[:hunt_missing_scenes]
    
    whisparr_logger.info(f"Selected {len(scenes_to_search)} missing scenes to search.")

    processed_in_this_run = set()
    # Process selected scenes
    for scene in scenes_to_search:
        # Check for stop signal before each scene
        if stop_check():
            whisparr_logger.info("Stop requested during scene processing. Aborting...")
            break
        
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_missing_scenes", 1)
        if scenes_processed >= current_limit:
             whisparr_logger.info(f"Reached HUNT_MISSING_SCENES limit ({current_limit}) for this cycle.")
             break

        scene_id = scene.get("id")
        title = scene.get("title", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        
        whisparr_logger.info(f"Processing missing scene: \"{title}\" - {season_episode} (Scene ID: {scene_id})")
        
        # Refresh the scene information if not skipped
        refresh_command_id = None
        if not skip_scene_refresh:
            whisparr_logger.info(" - Refreshing scene information...")
            refresh_command_id = whisparr_api.refresh_scene(api_url, api_key, api_timeout, scene_id)
            if refresh_command_id:
                whisparr_logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                time.sleep(5) # Basic wait
            else:
                whisparr_logger.warning(f"Failed to trigger refresh command for scene ID: {scene_id}. Proceeding without refresh.")
        else:
            whisparr_logger.info(" - Skipping scene refresh (skip_scene_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            whisparr_logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the scene
        whisparr_logger.info(" - Searching for missing scene...")
        search_command_id = whisparr_api.scene_search(api_url, api_key, api_timeout, [scene_id])
        if search_command_id:
            whisparr_logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            save_processed_ids(PROCESSED_MISSING_FILE, scene_id)
            processed_in_this_run.add(scene_id)
            scenes_processed += 1
            processing_done = True
            
            # Increment the hunted statistics for Whisparr
            increment_stat("whisparr", "hunted", 1)
            whisparr_logger.debug(f"Incremented whisparr hunted statistics by 1")

            # Log progress
            current_limit = app_settings.get("hunt_missing_scenes", 1)
            whisparr_logger.info(f"Processed {scenes_processed}/{current_limit} missing scenes this cycle.")
        else:
            whisparr_logger.warning(f"Failed to trigger search command for scene ID {scene_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if processed_in_this_run:
        whisparr_logger.info(f"Completed processing {len(processed_in_this_run)} missing scenes for this cycle.")
    else:
        whisparr_logger.info("No new missing scenes were processed in this run.")
        
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done