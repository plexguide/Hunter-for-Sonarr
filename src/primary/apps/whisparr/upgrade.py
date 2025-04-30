#!/usr/bin/env python3
"""
Quality Upgrade Processing for Whisparr
Handles searching for items that need quality upgrades in Whisparr

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
        True if any items were processed for upgrades, False otherwise.
    """
    whisparr_logger.info("Starting quality cutoff upgrades processing cycle for Whisparr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_item_refresh = app_settings.get("skip_item_refresh", False)
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
        whisparr_logger.info("'hunt_upgrade_items' setting is 0 or less. Skipping quality upgrade processing.")
        return False

    # Check for stop signal
    if stop_check():
        whisparr_logger.info("Stop requested before starting quality upgrades. Aborting...")
        return False

    # Get items eligible for upgrade
    whisparr_logger.info(f"Retrieving items eligible for cutoff upgrade using API v{api_version}...")
    upgrade_eligible_data = whisparr_api.get_cutoff_unmet_items(api_url, api_key, api_timeout, monitored_only, api_version)
    
    if not upgrade_eligible_data:
        whisparr_logger.info("No items found eligible for upgrade or error retrieving them.")
        return False
    
    # Check for stop signal after retrieving eligible items
    if stop_check():
        whisparr_logger.info("Stop requested after retrieving upgrade eligible items. Aborting...")
        return False
        
    whisparr_logger.info(f"Found {len(upgrade_eligible_data)} items eligible for quality upgrade.")
    
    items_processed = 0
    processing_done = False
    
    # Select items to upgrade based on configuration
    if random_upgrades:
        whisparr_logger.info(f"Randomly selecting up to {hunt_upgrade_items} items for quality upgrade.")
        items_to_upgrade = random.sample(upgrade_eligible_data, min(len(upgrade_eligible_data), hunt_upgrade_items))
    else:
        whisparr_logger.info(f"Selecting the first {hunt_upgrade_items} items for quality upgrade (sorted by title).")
        # Sort by title for consistent ordering if not random
        upgrade_eligible_data.sort(key=lambda x: x.get("title", ""))
        items_to_upgrade = upgrade_eligible_data[:hunt_upgrade_items]
    
    whisparr_logger.info(f"Selected {len(items_to_upgrade)} items for quality upgrade.")
    
    # Process selected items
    for item in items_to_upgrade:
        # Check for stop signal before each item
        if stop_check():
            whisparr_logger.info("Stop requested during item processing. Aborting...")
            break
            
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
        if items_processed >= current_limit:
            whisparr_logger.info(f"Reached HUNT_UPGRADE_ITEMS limit ({current_limit}) for this cycle.")
            break
        
        item_id = item.get("id")
        title = item.get("title", "Unknown Title")
        season_episode = f"S{item.get('seasonNumber', 0):02d}E{item.get('episodeNumber', 0):02d}"
        
        current_quality = item.get("episodeFile", {}).get("quality", {}).get("quality", {}).get("name", "Unknown")
        
        whisparr_logger.info(f"Processing item for quality upgrade: \"{title}\" - {season_episode} (Item ID: {item_id})")
        whisparr_logger.info(f" - Current quality: {current_quality}")
        
        # Refresh the item information if not skipped
        refresh_command_id = None
        if not skip_item_refresh:
            whisparr_logger.info(" - Refreshing item information...")
            refresh_command_id = whisparr_api.refresh_item(api_url, api_key, api_timeout, item_id, api_version)
            if refresh_command_id:
                whisparr_logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                time.sleep(5) # Basic wait
            else:
                whisparr_logger.warning(f"Failed to trigger refresh command for item ID: {item_id}. Proceeding without refresh.")
        else:
            whisparr_logger.info(" - Skipping item refresh (skip_item_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            whisparr_logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the item
        whisparr_logger.info(" - Searching for quality upgrade...")
        search_command_id = whisparr_api.item_search(api_url, api_key, api_timeout, [item_id], api_version)
        if search_command_id:
            whisparr_logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            items_processed += 1
            processing_done = True
            
            # Increment the upgraded statistics for Whisparr
            increment_stat("whisparr", "upgraded", 1)
            whisparr_logger.debug(f"Incremented whisparr upgraded statistics by 1")
            
            # Log progress
            current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
            whisparr_logger.info(f"Processed {items_processed}/{current_limit} items for quality upgrade this cycle.")
        else:
            whisparr_logger.warning(f"Failed to trigger search command for item ID {item_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if items_processed > 0:
        whisparr_logger.info(f"Completed processing {items_processed} items for quality upgrade for this cycle.")
    else:
        whisparr_logger.info("No new items were processed for quality upgrade in this run.")
        
    return processing_done