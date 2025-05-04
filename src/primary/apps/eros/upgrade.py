#!/usr/bin/env python3
"""
Quality Upgrade Processing for Eros
Handles searching for items that need quality upgrades in Eros

Exclusively supports the v3 API.
"""

import time
import random
import datetime
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.eros import api as eros_api
from src.primary.stats_manager import increment_stat
from src.primary.stateful_manager import is_processed, add_processed_id
from src.primary.utils.history_utils import log_processed_media
from src.primary.settings_manager import get_advanced_setting
from src.primary.state import check_state_reset

# Get logger for the app
eros_logger = get_logger("eros")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Eros based on settings.
    
    Args:
        app_settings: Dictionary containing all settings for Eros
        stop_check: A function that returns True if the process should stop
        
    Returns:
        True if any items were processed for upgrades, False otherwise.
    """
    eros_logger.info("Starting quality cutoff upgrades processing cycle for Eros.")
    processed_any = False
    
    # Reset state files if enough time has passed
    check_state_reset("eros")
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    instance_name = app_settings.get("instance_name", "Eros Default")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_item_refresh = app_settings.get("skip_item_refresh", False)
    search_mode = app_settings.get("search_mode", "movie")  # Default to movie mode if not specified
    
    eros_logger.info(f"Using search mode: {search_mode} for quality upgrades")
    
    # Use the new hunt_upgrade_items parameter name, falling back to hunt_upgrade_scenes for backwards compatibility
    hunt_upgrade_items = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 0))
    
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = get_advanced_setting("stateful_management_hours", 168)  
    
    # Log that we're using Eros API v3
    eros_logger.info(f"Using Eros API v3 for instance: {instance_name}")

    # Skip if hunt_upgrade_items is set to 0
    if hunt_upgrade_items <= 0:
        eros_logger.info("'hunt_upgrade_items' setting is 0 or less. Skipping quality upgrade processing.")
        return False

    # Check for stop signal
    if stop_check():
        eros_logger.info("Stop requested before starting quality upgrades. Aborting...")
        return False

    # Get items eligible for upgrade
    eros_logger.info(f"Retrieving items eligible for cutoff upgrade...")
    upgrade_eligible_data = eros_api.get_quality_upgrades(api_url, api_key, api_timeout, monitored_only, search_mode)
    
    if not upgrade_eligible_data:
        eros_logger.info("No items found eligible for upgrade or error retrieving them.")
        return False
    
    # Check for stop signal after retrieving eligible items
    if stop_check():
        eros_logger.info("Stop requested after retrieving upgrade eligible items. Aborting...")
        return False
        
    eros_logger.info(f"Found {len(upgrade_eligible_data)} items eligible for quality upgrade.")
    
    # Filter out already processed items using stateful management
    unprocessed_items = []
    for item in upgrade_eligible_data:
        item_id = str(item.get("id"))
        if not is_processed("eros", instance_name, item_id):
            unprocessed_items.append(item)
        else:
            eros_logger.debug(f"Skipping already processed item ID: {item_id}")
    
    eros_logger.info(f"Found {len(unprocessed_items)} unprocessed items out of {len(upgrade_eligible_data)} total items eligible for quality upgrade.")
    
    if not unprocessed_items:
        eros_logger.info(f"No unprocessed items found for {instance_name}. All available items have been processed.")
        return False
    
    items_processed = 0
    processing_done = False
    
    # Always use random selection for upgrades
    eros_logger.info(f"Randomly selecting up to {hunt_upgrade_items} items for quality upgrade.")
    items_to_upgrade = random.sample(unprocessed_items, min(len(unprocessed_items), hunt_upgrade_items))
    
    eros_logger.info(f"Selected {len(items_to_upgrade)} items for quality upgrade.")
    
    # Process selected items
    for item in items_to_upgrade:
        # Check for stop signal before each item
        if stop_check():
            eros_logger.info("Stop requested during item processing. Aborting...")
            break
            
        # Re-check limit in case it changed
        current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
        if items_processed >= current_limit:
            eros_logger.info(f"Reached HUNT_UPGRADE_ITEMS limit ({current_limit}) for this cycle.")
            break
        
        item_id = item.get("id")
        title = item.get("title", "Unknown Title")
        season_episode = f"S{item.get('seasonNumber', 0):02d}E{item.get('episodeNumber', 0):02d}"
        
        current_quality = item.get("episodeFile", {}).get("quality", {}).get("quality", {}).get("name", "Unknown")
        
        eros_logger.info(f"Processing item for quality upgrade: \"{title}\" - {season_episode} (Item ID: {item_id})")
        eros_logger.info(f" - Current quality: {current_quality}")
        
        # Mark the item as processed BEFORE triggering any searches
        add_processed_id("eros", instance_name, str(item_id))
        eros_logger.debug(f"Added item ID {item_id} to processed list for {instance_name}")
        
        # Refresh the item information if not skipped
        refresh_command_id = None
        if not skip_item_refresh:
            eros_logger.info(" - Refreshing item information...")
            refresh_command_id = eros_api.refresh_item(api_url, api_key, api_timeout, item_id)
            if refresh_command_id:
                eros_logger.info(f"Triggered refresh command {refresh_command_id}. Waiting a few seconds...")
                time.sleep(5) # Basic wait
            else:
                eros_logger.warning(f"Failed to trigger refresh command for item ID: {item_id}. Proceeding without refresh.")
        else:
            eros_logger.info(" - Skipping item refresh (skip_item_refresh=true)")
        
        # Check for stop signal before searching
        if stop_check():
            eros_logger.info(f"Stop requested before searching for {title}. Aborting...")
            break
        
        # Search for the item
        eros_logger.info(" - Searching for quality upgrade...")
        search_command_id = eros_api.item_search(api_url, api_key, api_timeout, [item_id])
        if search_command_id:
            eros_logger.info(f"Triggered search command {search_command_id}. Assuming success for now.")
            
            # Log to history so the upgrade appears in the history UI
            series_title = item.get("series", {}).get("title", "Unknown Series")
            media_name = f"{series_title} - {season_episode} - {title}"
            log_processed_media("eros", media_name, item_id, instance_name, "upgrade")
            eros_logger.debug(f"Logged quality upgrade to history for item ID {item_id}")
            
            items_processed += 1
            processing_done = True
            
            # Increment the upgraded statistics for Eros
            increment_stat("eros", "upgraded", 1)
            eros_logger.debug(f"Incremented eros upgraded statistics by 1")
            
            # Log progress
            current_limit = app_settings.get("hunt_upgrade_items", app_settings.get("hunt_upgrade_scenes", 1))
            eros_logger.info(f"Processed {items_processed}/{current_limit} items for quality upgrade this cycle.")
        else:
            eros_logger.warning(f"Failed to trigger search command for item ID {item_id}.")
            # Do not mark as processed if search couldn't be triggered
            continue
    
    # Log final status
    if items_processed > 0:
        eros_logger.info(f"Completed processing {items_processed} items for quality upgrade for this cycle.")
    else:
        eros_logger.info("No new items were processed for quality upgrade in this run.")
        
    return processing_done
