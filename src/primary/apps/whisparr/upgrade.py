#!/usr/bin/env python3
"""
Quality Upgrade Processing for Whisparr
Handles searching for scenes that need quality upgrades in Whisparr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional, Any
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path
from src.primary.apps.whisparr.api import get_cutoff_unmet_scenes, refresh_scene, scene_search
from src.primary.stats_manager import increment_stat  # Import the stats increment function

# Get app-specific logger
logger = get_logger("whisparr")

def process_cutoff_upgrades(app_settings: Dict[str, Any], restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process quality upgrades for scenes that don't meet the cutoff.
    
    Args:
        app_settings: Dictionary containing all settings for Whisparr.
        restart_cycle_flag: Function that returns True if processing should restart.
        
    Returns:
        True if any scenes were upgraded, False otherwise
    """
    # Get settings from the passed dictionary
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 60)
    hunt_upgrade_scenes = app_settings.get("hunt_upgrade_scenes", 1)
    random_upgrades = app_settings.get("random_upgrades", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    monitored_only = app_settings.get("monitored_only", True)
    
    # Get app-specific state file
    PROCESSED_UPGRADES_FILE = get_state_file_path("whisparr", "processed_upgrades")
    
    logger.info("=== Checking for Quality Upgrades ===")
    
    if not api_url or not api_key:
        logger.error("API URL or Key not configured in settings. Cannot process quality upgrades.")
        return False
        
    # Skip if hunt_upgrade_scenes is set to 0
    if hunt_upgrade_scenes <= 0:
        logger.info("'hunt_upgrade_scenes' setting is 0 or less. Skipping quality upgrade processing.")
        return False
        
    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Restart signal received before starting upgrades. Aborting...")
        return False
        
    # Get scenes with quality below cutoff
    logger.info("Retrieving scenes below quality cutoff...")
    cutoff_unmet_scenes = get_cutoff_unmet_scenes(api_url, api_key, api_timeout, monitored_only)
    
    if cutoff_unmet_scenes is None:  # API call failed
        logger.error("Failed to retrieve cutoff unmet scenes from Whisparr API.")
        return False
        
    if not cutoff_unmet_scenes:
        logger.info("No scenes found that need quality upgrades.")
        return False
        
    # Check for restart signal after retrieving scenes
    if restart_cycle_flag():
        logger.info("🔄 Restart signal received after retrieving scenes. Aborting...")
        return False
        
    logger.info(f"Found {len(cutoff_unmet_scenes)} scenes that need quality upgrades.")
    
    # Load already processed upgrade IDs
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADES_FILE)
    
    # Filter out already processed scenes
    logger.debug(f"Filtering out {len(processed_upgrade_ids)} already processed scenes...")
    unprocessed_scenes = [scene for scene in cutoff_unmet_scenes if scene.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_scenes:
        logger.info("All scenes below cutoff have already been processed recently. Skipping.")
        return False
        
    logger.info(f"Found {len(unprocessed_scenes)} scenes below cutoff that haven't been processed recently.")
    
    # Select scenes to process
    scenes_to_process = []
    if random_upgrades:
        logger.info(f"Randomly selecting {hunt_upgrade_scenes} scene(s) for quality upgrade.")
        scenes_to_process = random.sample(unprocessed_scenes, min(len(unprocessed_scenes), hunt_upgrade_scenes))
    else:
        logger.info(f"Selecting first {hunt_upgrade_scenes} scene(s) for quality upgrade.")
        # Sort by title for consistent ordering
        unprocessed_scenes.sort(key=lambda x: x.get("title", ""))
        scenes_to_process = unprocessed_scenes[:hunt_upgrade_scenes]
        
    # List selected scenes
    logger.info("Selected scenes for quality upgrade:")
    for idx, scene in enumerate(scenes_to_process):
        title = scene.get("title", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        scene_id = scene.get("id")
        quality_name = "Unknown"
        if "episodeFile" in scene and scene["episodeFile"]:
            quality = scene["episodeFile"].get("quality", {})
            quality_name = quality.get("quality", {}).get("name", "Unknown")
        logger.info(f" {idx+1}. \"{title}\" - {season_episode} - Current quality: {quality_name} (ID: {scene_id})")
    
    # Process up to hunt_upgrade_scenes scenes
    scenes_processed = 0
    processing_done = False
    for scene in scenes_to_process:
        # Check for restart signal before each scene
        if restart_cycle_flag():
            logger.info("🔄 Received restart signal during scene processing. Aborting...")
            break
            
        title = scene.get("title", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        scene_id = scene.get("id")
        quality_info = ""
        if "episodeFile" in scene and scene["episodeFile"]:
            quality = scene["episodeFile"].get("quality", {})
            quality_name = quality.get("quality", {}).get("name", "Unknown")
            quality_info = f" - Current quality: {quality_name}"
        
        logger.info(f"Processing quality upgrade for: \"{title}\" - {season_episode}{quality_info} (Scene ID: {scene_id})")
        
        # Refresh the scene information if skip_scene_refresh is false
        if not skip_scene_refresh:
            logger.info(" - Refreshing scene information...")
            refresh_res = refresh_scene(api_url, api_key, api_timeout, scene_id)
            if not refresh_res:
                logger.warning("WARNING: Refresh command failed. Skipping this scene.")
                continue
            logger.info(f"Refresh command completed successfully.")
            
            # Small delay after refresh to allow Whisparr to process
            time.sleep(2)
        else:
            logger.info(" - Skipping scene refresh (skip_scene_refresh=true)")
        
        # Check for restart signal before searching
        if restart_cycle_flag():
            logger.info(f"🔄 Received restart signal before searching for {title}. Aborting...")
            break
        
        # Search for the scene
        logger.info(" - Searching for quality upgrade...")
        search_res = scene_search(api_url, api_key, api_timeout, [scene_id])
        if search_res:
            logger.info(f"Search command triggered successfully. Marking scene as processed.")
            # Mark this scene as processed
            save_processed_id(PROCESSED_UPGRADES_FILE, scene_id)
            scenes_processed += 1
            processing_done = True
            
            # Increment the upgraded statistics for Whisparr
            increment_stat("whisparr", "upgraded", 1)
            logger.debug(f"Incremented whisparr upgraded statistics by 1")
            
            # Log progress
            logger.info(f"Processed {scenes_processed}/{len(scenes_to_process)} quality upgrades this cycle.")
        else:
            logger.error(f"Failed to trigger search for scene ID {scene_id}. Skipping.")
    
    # Final log message
    if scenes_processed > 0:
        logger.info(f"Completed {scenes_processed} scene quality upgrades.")
    else:
        logger.info("No scene quality upgrades were processed.")
        
    # Consider truncating the list to keep it manageable
    truncate_processed_list(PROCESSED_UPGRADES_FILE)
        
    return processing_done