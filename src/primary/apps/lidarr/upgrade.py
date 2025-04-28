#!/usr/bin/env python3
"""
Lidarr cutoff upgrade processing module for Huntarr
Handles albums that do not meet the configured quality cutoff.
"""

import time
import random
from typing import Dict, Any, Optional, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
lidarr_logger = get_logger(__name__) # Use __name__ for correct logger hierarchy

def process_cutoff_upgrades(
    instance_config: Dict[str, Any],
    general_settings: Dict[str, Any],
    stop_event_check: Optional[Callable[[], bool]] = None
) -> bool:
    """
    Processes cutoff upgrades for albums in a specific Lidarr instance.

    Args:
        instance_config (dict): Dictionary containing instance-specific details 
                                  (instance_name, api_url, api_key).
        general_settings (dict): Dictionary containing general Lidarr settings 
                                  (hunt_upgrade_items, monitored_only, etc.).
        stop_event_check (Optional[Callable[[], bool]]): Function to check if shutdown is requested.
                                                     Defaults to None.

    Returns:
        bool: True if any items were processed, False otherwise.
    """
    
    # Extract instance-specific details
    instance_name = instance_config.get("instance_name", "Lidarr Default")
    api_url = instance_config.get("api_url")
    api_key = instance_config.get("api_key")

    # Extract general settings
    hunt_upgrade_items = general_settings.get("hunt_upgrade_items", 0)
    monitored_only = general_settings.get("monitored_only", True)
    random_upgrades = general_settings.get("random_upgrades", True) # Renamed from random_missing
    api_timeout = general_settings.get("api_timeout", 120)
    command_wait_delay = general_settings.get("command_wait_delay", 1)
    command_wait_attempts = general_settings.get("command_wait_attempts", 600)

    lidarr_logger.debug(f"Processing upgrades for instance: {instance_name}")
    lidarr_logger.debug(f"Instance Config: {instance_config}")
    lidarr_logger.debug(f"General Settings: {general_settings}")

    # Check if API URL or Key are missing
    if not api_url or not api_key:
        lidarr_logger.error(f"Missing API URL or Key for instance '{instance_name}'. Cannot process upgrades.")
        return False

    # Check if upgrade hunting is enabled
    if hunt_upgrade_items <= 0:
        lidarr_logger.info(f"'hunt_upgrade_items' is {hunt_upgrade_items} or less. Skipping upgrade processing for {instance_name}.")
        return False

    processed_count = 0
    total_items_to_process = hunt_upgrade_items

    try:
        lidarr_logger.info(f"Fetching cutoff unmet albums for {instance_name}...")
        # Pass necessary details extracted above to the API function
        cutoff_unmet_albums = lidarr_api.get_cutoff_unmet(
            api_url,
            api_key,
            monitored_only=monitored_only,
            api_timeout=api_timeout
        )

        if not cutoff_unmet_albums:
            lidarr_logger.info(f"No cutoff unmet albums found for {instance_name}.")
            return False

        lidarr_logger.info(f"Found {len(cutoff_unmet_albums)} cutoff unmet albums for {instance_name}.")

        # Select albums to search
        if random_upgrades: # Use the correct setting name
            albums_to_search = random.sample(cutoff_unmet_albums, min(len(cutoff_unmet_albums), total_items_to_process))
            lidarr_logger.debug(f"Randomly selected {len(albums_to_search)} albums out of {len(cutoff_unmet_albums)} to search for upgrades.")
        else:
            albums_to_search = cutoff_unmet_albums[:total_items_to_process]
            lidarr_logger.debug(f"Selected the first {len(albums_to_search)} albums out of {len(cutoff_unmet_albums)} to search for upgrades.")

        album_ids_to_search = [album['id'] for album in albums_to_search]

        if not album_ids_to_search:
             lidarr_logger.info("No album IDs selected for upgrade search. Skipping trigger.")
             return False
        
        # Check stop event before triggering search
        if stop_event_check and stop_event_check():
            lidarr_logger.warning("Shutdown requested, stopping upgrade album search.")
            return False # Return False as no search was triggered in this case

        lidarr_logger.info(f"Triggering Album Search for {len(album_ids_to_search)} albums for upgrade on instance {instance_name}: {album_ids_to_search}")
        # Pass necessary details extracted above to the API function
        command_id = lidarr_api.trigger_album_search(
            api_url,
            api_key,
            album_ids_to_search,
            api_timeout=api_timeout
        )
        if command_id:
            lidarr_logger.debug(f"Upgrade album search command triggered with ID: {command_id} for albums: {album_ids_to_search}")
            increment_stat("lidarr", "upgraded") # Use appropriate stat key
            time.sleep(command_wait_delay) # Basic delay
            processed_count += len(album_ids_to_search)
            # Consider adding wait_for_command logic if needed
            # wait_for_command(api_url, api_key, command_id, command_wait_delay, command_wait_attempts)
        else:
            lidarr_logger.warning(f"Failed to trigger upgrade album search for IDs {album_ids_to_search} on {instance_name}.")

    except Exception as e:
        lidarr_logger.error(f"An error occurred during upgrade album processing for {instance_name}: {e}", exc_info=True)
        return False # Indicate failure

    lidarr_logger.info(f"Upgrade album processing finished for {instance_name}. Triggered searches for {processed_count} items.")
    return processed_count > 0