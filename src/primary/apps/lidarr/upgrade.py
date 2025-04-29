#!/usr/bin/env python3
"""
Lidarr cutoff upgrade processing module for Huntarr
Handles albums that do not meet the configured quality cutoff.
"""

import time
import random
from typing import Dict, Any, Optional, Callable, List # Added List
from src.primary.utils.logger import get_logger
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
lidarr_logger = get_logger(__name__) # Use __name__ for correct logger hierarchy

def process_cutoff_upgrades(
    app_settings: Dict[str, Any], # Changed signature: Use app_settings
    stop_check: Callable[[], bool] # Changed signature: Use stop_check
) -> bool:
    """
    Processes cutoff upgrades for albums in a specific Lidarr instance.

    Args:
        app_settings (dict): Dictionary containing combined instance and general Lidarr settings.
        stop_check (Callable[[], bool]): Function to check if shutdown is requested.

    Returns:
        bool: True if any items were processed, False otherwise.
    """
    lidarr_logger.info("Starting quality cutoff upgrades processing cycle for Lidarr.")
    processed_any = False

    # --- Extract Settings --- #
    # Instance details are now part of app_settings passed from background loop
    instance_name = app_settings.get("instance_name", "Lidarr Default")
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")

    # General Lidarr settings (also from app_settings)
    hunt_upgrade_items = app_settings.get("hunt_upgrade_items", 0)
    monitored_only = app_settings.get("monitored_only", True)
    random_upgrades = app_settings.get("random_upgrades", True)
    api_timeout = app_settings.get("api_timeout", 120)
    command_wait_delay = app_settings.get("command_wait_delay", 1)
    command_wait_attempts = app_settings.get("command_wait_attempts", 600)

    lidarr_logger.debug(f"Processing upgrades for instance: {instance_name}")
    # lidarr_logger.debug(f"Instance Config (extracted): {{ 'api_url': '{api_url}', 'api_key': '***' }}")
    # lidarr_logger.debug(f"General Settings (from app_settings): {app_settings}") # Avoid logging full settings potentially containing sensitive info

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
        # Corrected function name from get_cutoff_unmet to get_cutoff_unmet_albums
        cutoff_unmet_albums = lidarr_api.get_cutoff_unmet_albums(
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
        albums_to_search: List[Dict[str, Any]] = [] # Ensure type hint
        if random_upgrades:
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
        if stop_check and stop_check(): # Use the passed stop_check function
            lidarr_logger.warning("Shutdown requested, stopping upgrade album search.")
            return False # Return False as no search was triggered in this case

        lidarr_logger.info(f"Triggering Album Search for {len(album_ids_to_search)} albums for upgrade on instance {instance_name}: {album_ids_to_search}")
        # Pass necessary details extracted above to the API function
        command_id = lidarr_api.search_albums(
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
            processed_any = True # Mark that we processed something
            # Consider adding wait_for_command logic if needed
            # wait_for_command(api_url, api_key, command_id, command_wait_delay, command_wait_attempts)
        else:
            lidarr_logger.warning(f"Failed to trigger upgrade album search for IDs {album_ids_to_search} on {instance_name}.")

    except Exception as e:
        lidarr_logger.error(f"An error occurred during upgrade album processing for {instance_name}: {e}", exc_info=True)
        return False # Indicate failure

    lidarr_logger.info(f"Upgrade album processing finished for {instance_name}. Triggered searches for {processed_count} items.")
    return processed_any # Return True if anything was processed