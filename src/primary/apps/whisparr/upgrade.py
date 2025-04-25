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

# Get app-specific logger
logger = get_logger("whisparr")

def process_cutoff_upgrades(app_settings: Dict[str, Any], restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process scenes that need quality upgrades (cutoff unmet).
    
    Args:
        app_settings: Dictionary containing settings for Whisparr.
        restart_cycle_flag: Function that returns whether to restart the cycle
    
    Returns:
        True if any processing was done, False otherwise
    """
    # Get settings from the passed dictionary
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)
    hunt_upgrade_scenes = app_settings.get("hunt_upgrade_scenes", 0)
    random_upgrades = app_settings.get("random_upgrades", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    monitored_only = app_settings.get("monitored_only", True)
    
    # Get app-specific state file
    PROCESSED_UPGRADE_FILE = get_state_file_path("whisparr", "processed_upgrades")

    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")

    # Skip if hunt_upgrade_scenes is set to 0
    if hunt_upgrade_scenes <= 0:
        logger.info("hunt_upgrade_scenes is set to 0, skipping quality upgrades")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting quality upgrades. Aborting...")
        return False
    
    # Get scenes needing quality upgrades
    logger.info("Retrieving scenes that need quality upgrades...")
    upgrade_scenes = get_cutoff_unmet_scenes(api_url, api_key, api_timeout, monitored_only)
    
    if not upgrade_scenes:
        logger.info("No scenes found that need quality upgrades.")
        return False
    
    # Check for restart signal after retrieving scenes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal after retrieving upgrade scenes. Aborting...")
        return False
    
    logger.info(f"Found {len(upgrade_scenes)} scenes that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    
    # Filter out already processed scenes
    unprocessed_scenes = [scene for scene in upgrade_scenes if scene.get("id") not in processed_upgrade_ids]
    
    if not unprocessed_scenes:
        logger.info("All upgrade scenes have already been processed. Skipping.")
        return False
    
    logger.info(f"Found {len(unprocessed_scenes)} upgrade scenes that haven't been processed yet.")
    
    # Randomize if requested
    if random_upgrades:
        logger.info("Using random selection for quality upgrades (RANDOM_UPGRADES=true)")
        random.shuffle(unprocessed_scenes)
    else:
        logger.info("Using sequential selection for quality upgrades (RANDOM_UPGRADES=false)")
        # Sort by title for consistent ordering
        unprocessed_scenes.sort(key=lambda x: x.get("sceneName", ""))
    
    # Check for restart signal before processing scenes
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before processing scenes. Aborting...")
        return False
    
    # Create a list of scenes to process, limited by hunt_upgrade_scenes
    scenes_to_process = unprocessed_scenes[:min(len(unprocessed_scenes), hunt_upgrade_scenes)]
    
    # Log a summary of all scenes that will be processed
    if scenes_to_process:
        logger.info(f"Selected {len(scenes_to_process)} scenes for quality upgrades this cycle:")
        for idx, scene in enumerate(scenes_to_process):
            title = scene.get("sceneName", "Unknown Title")
            season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
            scene_id = scene.get("id")
            quality_name = "Unknown"
            if "sceneFile" in scene and scene["sceneFile"]:
                quality = scene["sceneFile"].get("quality", {})
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
        
        # Check again for the current limit in case it was changed during processing
        current_limit = app_settings.get("hunt_upgrade_scenes", 0)
        
        if scenes_processed >= current_limit:
            logger.info(f"Reached hunt_upgrade_scenes={current_limit} for this cycle.")
            break
        
        scene_id = scene.get("id")
        title = scene.get("sceneName", "Unknown Title")
        season_episode = f"S{scene.get('seasonNumber', 0):02d}E{scene.get('episodeNumber', 0):02d}"
        
        # Get quality information
        quality_info = ""
        if "sceneFile" in scene and scene["sceneFile"]:
            quality = scene["sceneFile"].get("quality", {})
            quality_name = quality.get("quality", {}).get("name", "Unknown")
            quality_info = f" (Current quality: {quality_name})"
        
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
            logger.info(f"Search command completed successfully.")
            # Mark as processed
            save_processed_id(PROCESSED_UPGRADE_FILE, scene_id)
            scenes_processed += 1
            processing_done = True
            
            # Log with the current limit, not the initial one
            current_limit = app_settings.get("hunt_upgrade_scenes", 0)
            logger.info(f"Processed {scenes_processed}/{current_limit} upgrade scenes this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for scene ID {scene_id}.")
            continue
    
    # Log final status
    current_limit = app_settings.get("hunt_upgrade_scenes", 0)
    logger.info(f"Completed processing {scenes_processed} upgrade scenes this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done