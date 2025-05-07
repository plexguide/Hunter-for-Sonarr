#!/usr/bin/env python3
"""
Huntarr - Main entry point for the application
Supports multiple Arr applications running concurrently
"""

import time
import sys
import os
# import socket # No longer used directly
import signal
import importlib
import logging
import threading
from typing import Dict, List, Optional, Callable, Union, Tuple
import json
from datetime import datetime, timedelta

# Define the version number
__version__ = "1.0.0" # Consider updating this based on changes

# Set up logging first
from src.primary.utils.logger import setup_main_logger, get_logger # Import get_logger
logger = setup_main_logger()

# Import necessary modules
from src.primary import config, settings_manager
# Removed keys_manager import as settings_manager handles API details
from src.primary.state import check_state_reset, calculate_reset_time
# from src.primary.utils.app_utils import get_ip_address # No longer used here
from src.primary.utils.hunting_manager import HuntingManager

# Track active threads and stop flag
app_threads: Dict[str, threading.Thread] = {}
stop_event = threading.Event() # Use an event for clearer stop signaling

# Add global for hunting manager thread
hunting_manager_thread = None
hunting_manager_stop_event = threading.Event()

def app_specific_loop(app_type: str) -> None:
    """
    Main processing loop for a specific Arr application.

    Args:
        app_type: The type of Arr application (sonarr, radarr, lidarr, readarr)
    """
    app_logger = get_logger(app_type)
    app_logger.info(f"=== [{app_type.upper()}] Thread starting ===")

    # Dynamically import app-specific modules
    process_missing = None
    process_upgrades = None
    get_queue_size = None
    check_connection = None
    get_instances_func = None # Default: No multi-instance function found
    hunt_missing_setting = ""
    hunt_upgrade_setting = ""

    try:
        # Import the main app module first to check for get_configured_instances
        app_module = importlib.import_module(f'src.primary.apps.{app_type}')
        app_logger.debug(f"Attributes found in {app_module.__name__}: {dir(app_module)}")
        api_module = importlib.import_module(f'src.primary.apps.{app_type}.api')
        missing_module = importlib.import_module(f'src.primary.apps.{app_type}.missing')
        upgrade_module = importlib.import_module(f'src.primary.apps.{app_type}.upgrade')

        # Try to get the multi-instance function from the main app module
        try:
            get_instances_func = getattr(app_module, 'get_configured_instances')
            app_logger.debug(f"Found 'get_configured_instances' in {app_module.__name__}")
        except AttributeError:
            app_logger.debug(f"'get_configured_instances' not found in {app_module.__name__}. Assuming single instance mode.")
            get_instances_func = None # Explicitly set to None if not found

        check_connection = getattr(api_module, 'check_connection')
        get_queue_size = getattr(api_module, 'get_download_queue_size', lambda api_url, api_key, api_timeout: 0) # Default if not found

        if app_type == "sonarr":
            missing_module = importlib.import_module('src.primary.apps.sonarr.missing')
            upgrade_module = importlib.import_module('src.primary.apps.sonarr.upgrade')
            process_missing = getattr(missing_module, 'process_missing_episodes')
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_items"
            hunt_upgrade_setting = "hunt_upgrade_items"
        elif app_type == "radarr":
            missing_module = importlib.import_module('src.primary.apps.radarr.missing')
            upgrade_module = importlib.import_module('src.primary.apps.radarr.upgrade')
            process_missing = getattr(missing_module, 'process_missing_movies')
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_movies"
            hunt_upgrade_setting = "hunt_upgrade_movies"
        elif app_type == "lidarr":
            missing_module = importlib.import_module('src.primary.apps.lidarr.missing')
            upgrade_module = importlib.import_module('src.primary.apps.lidarr.upgrade')
            # Use process_missing_albums as the function name
            process_missing = getattr(missing_module, 'process_missing_albums') 
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_items"
            # Use hunt_upgrade_items
            hunt_upgrade_setting = "hunt_upgrade_items" 
        elif app_type == "readarr":
            missing_module = importlib.import_module('src.primary.apps.readarr.missing')
            upgrade_module = importlib.import_module('src.primary.apps.readarr.upgrade')
            process_missing = getattr(missing_module, 'process_missing_books')
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_books"
            hunt_upgrade_setting = "hunt_upgrade_books"
        elif app_type == "whisparr":
            missing_module = importlib.import_module('src.primary.apps.whisparr.missing')
            upgrade_module = importlib.import_module('src.primary.apps.whisparr.upgrade')
            process_missing = getattr(missing_module, 'process_missing_scenes')
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_items"  # Updated to new name
            hunt_upgrade_setting = "hunt_upgrade_items"  # Updated to new name
        elif app_type == "eros":
            missing_module = importlib.import_module('src.primary.apps.eros.missing')
            upgrade_module = importlib.import_module('src.primary.apps.eros.upgrade')
            process_missing = getattr(missing_module, 'process_missing_items')
            process_upgrades = getattr(upgrade_module, 'process_cutoff_upgrades')
            hunt_missing_setting = "hunt_missing_items"
            hunt_upgrade_setting = "hunt_upgrade_items"
        else:
            app_logger.error(f"Unsupported app_type: {app_type}")
            return # Exit thread if app type is invalid

    except (ImportError, AttributeError) as e:
        app_logger.error(f"Failed to import modules or functions for {app_type}: {e}", exc_info=True)
        return # Exit thread if essential modules fail to load

    # Create app-specific logger using provided function
    app_logger = logging.getLogger(f"huntarr.{app_type}")
    
    while not stop_event.is_set():
        # --- Load Settings for this Cycle --- #
        try:
            # Load all settings for this app for the current cycle
            app_settings = settings_manager.load_settings(app_type) # Corrected function name
            if not app_settings: # Handle case where loading fails
                app_logger.error("Failed to load settings. Skipping cycle.")
                stop_event.wait(60) # Wait a minute before retrying
                continue

            # Get global settings needed for cycle timing
            sleep_duration = app_settings.get("sleep_duration", 900)
            api_timeout = app_settings.get("api_timeout", 120) # Default to 120 seconds

        except Exception as e:
            app_logger.error(f"Error loading settings for cycle: {e}", exc_info=True)
            stop_event.wait(60) # Wait before retrying
            continue

        # --- State Reset Check --- #
        check_state_reset(app_type)

        app_logger.info(f"=== Starting {app_type.upper()} cycle ===")

        # Check if we need to use multi-instance mode
        instances_to_process = []
        
        # Use the dynamically loaded function (if found)
        if get_instances_func:
            # Multi-instance mode supported
            try:
                instances_to_process = get_instances_func() # Call the dynamically loaded function
                if instances_to_process:
                    app_logger.info(f"Found {len(instances_to_process)} configured {app_type} instances to process")
                else:
                    # No instances found via get_configured_instances
                    app_logger.warning(f"No configured {app_type} instances found. Skipping cycle.")
                    stop_event.wait(sleep_duration)
                    continue
            except Exception as e:
                app_logger.error(f"Error calling get_configured_instances function: {e}", exc_info=True)
                stop_event.wait(60)
                continue
        else:
            # get_instances_func is None (either not defined in app module or import failed earlier)
            # Fallback to single instance mode using base settings if available
            api_url = app_settings.get("api_url")
            api_key = app_settings.get("api_key")
            instance_name = app_settings.get("name", f"{app_type.capitalize()} Default") # Use 'name' or default
            
            if api_url and api_key:
                app_logger.info(f"Processing {app_type} as single instance: {instance_name}")
                # Create a list with a single dict matching the multi-instance structure
                instances_to_process = [{
                    "instance_name": instance_name, 
                    "api_url": api_url, 
                    "api_key": api_key
                }]
            else:
                app_logger.warning(f"No 'get_configured_instances' function found and no valid single instance config (URL/Key) for {app_type}. Skipping cycle.")
                stop_event.wait(sleep_duration)
                continue
            
        # If after all checks, instances_to_process is still empty
        if not instances_to_process:
            app_logger.warning(f"No valid {app_type} instances to process this cycle (unexpected state). Skipping.")
            stop_event.wait(sleep_duration)
            continue
            
        # Process each instance dictionary returned by get_configured_instances
        processed_any_items = False
        for instance_details in instances_to_process:
            if stop_event.is_set():
                break
                
            instance_name = instance_details.get("instance_name", "Default") # Use the dict from get_configured_instances
            app_logger.info(f"Processing {app_type} instance: {instance_name}")
            
            # Get instance-specific settings from the instance_details dict
            api_url = instance_details.get("api_url", "")
            api_key = instance_details.get("api_key", "")

            # Get global/shared settings from app_settings loaded at the start of the loop
            # Example: monitored_only = app_settings.get("monitored_only", True)

            # --- Connection Check --- #
            if not api_url or not api_key:
                app_logger.warning(f"Missing API URL or Key for instance '{instance_name}'. Skipping.")
                continue
            try:
                # Use instance details for connection check
                app_logger.debug(f"Checking connection to {app_type} instance '{instance_name}' at {api_url} with timeout {api_timeout}s")
                connected = check_connection(api_url, api_key, api_timeout=api_timeout)
                if not connected:
                    app_logger.warning(f"Failed to connect to {app_type} instance '{instance_name}' at {api_url}. Skipping.")
                    continue
                app_logger.info(f"Successfully connected to {app_type} instance: {instance_name}")
            except Exception as e:
                app_logger.error(f"Error connecting to {app_type} instance '{instance_name}': {e}", exc_info=True)
                continue # Skip this instance if connection fails

            # --- Check if Hunt Modes are Enabled --- #
            # These checks use the hunt_missing_setting/hunt_upgrade_setting defined earlier
            # which correspond to keys in the main app_settings dict (e.g., 'hunt_missing_items')
            hunt_missing_value = app_settings.get(hunt_missing_setting, 0)
            hunt_upgrade_value = app_settings.get(hunt_upgrade_setting, 0)

            hunt_missing_enabled = hunt_missing_value > 0
            hunt_upgrade_enabled = hunt_upgrade_value > 0

            # --- Queue Size Check --- # Moved inside loop
            # Get maximum_download_queue_size from general settings (still using minimum_download_queue_size key for backward compatibility)
            general_settings = settings_manager.load_settings('general')
            max_queue_size = general_settings.get("minimum_download_queue_size", -1)
            app_logger.info(f"Using maximum download queue size: {max_queue_size} from general settings")
            
            if max_queue_size >= 0:
                try:
                    # Use instance details for queue check
                    current_queue_size = get_queue_size(api_url, api_key, api_timeout)
                    if current_queue_size >= max_queue_size:
                        app_logger.info(f"Download queue size ({current_queue_size}) meets or exceeds maximum ({max_queue_size}) for {instance_name}. Skipping cycle for this instance.")
                        continue # Skip processing for this instance
                    else:
                        app_logger.info(f"Queue size ({current_queue_size}) is below maximum ({max_queue_size}). Proceeding.")
                except Exception as e:
                    app_logger.warning(f"Could not get download queue size for {instance_name}. Proceeding anyway. Error: {e}", exc_info=False) # Log less verbosely
            
            # Prepare args dictionary for processing functions
            # Combine instance details with general app settings for the processing functions
            # Assuming app_settings already contains most general settings, add instance specifics
            combined_settings = app_settings.copy() # Start with general settings
            combined_settings.update(instance_details) # Add/overwrite with instance specifics (name, url, key)
            
            # Ensure settings from general.json are consistently used for all apps
            combined_settings["api_timeout"] = settings_manager.get_advanced_setting("api_timeout", 120)
            combined_settings["command_wait_delay"] = settings_manager.get_advanced_setting("command_wait_delay", 1)
            combined_settings["command_wait_attempts"] = settings_manager.get_advanced_setting("command_wait_attempts", 600)
            
            # Define the stop check function
            stop_check_func = stop_event.is_set

            # --- Process Missing --- #
            if hunt_missing_enabled and process_missing:
                try:
                    # Extract settings for direct function calls
                    api_url = combined_settings.get("api_url", "").strip()
                    api_key = combined_settings.get("api_key", "").strip()
                    api_timeout = combined_settings.get("api_timeout", 120)
                    monitored_only = combined_settings.get("monitored_only", True)
                    skip_future_episodes = combined_settings.get("skip_future_episodes", True)
                    skip_series_refresh = combined_settings.get("skip_series_refresh", False)
                    hunt_missing_items = combined_settings.get("hunt_missing_items", 0)
                    hunt_missing_mode = combined_settings.get("hunt_missing_mode", "episodes")
                    command_wait_delay = combined_settings.get("command_wait_delay", 1)
                    command_wait_attempts = combined_settings.get("command_wait_attempts", 600)
                    
                    if app_type == "sonarr":
                        processed_missing = process_missing(
                            api_url=api_url,
                            api_key=api_key,
                            instance_name=instance_name,  # Added the required instance_name parameter
                            api_timeout=api_timeout,
                            monitored_only=monitored_only,
                            skip_future_episodes=skip_future_episodes,
                            skip_series_refresh=skip_series_refresh,
                            hunt_missing_items=hunt_missing_items,
                            hunt_missing_mode=hunt_missing_mode,
                            command_wait_delay=command_wait_delay,
                            command_wait_attempts=command_wait_attempts,
                            stop_check=stop_check_func
                        )
                    else:
                        # For other apps that still use the old signature
                        processed_missing = process_missing(app_settings=combined_settings, stop_check=stop_check_func)
                        
                    if processed_missing:
                        processed_any_items = True
                except Exception as e:
                    app_logger.error(f"Error during missing processing for {instance_name}: {e}", exc_info=True)

            # --- Process Upgrades --- #
            if hunt_upgrade_enabled and process_upgrades:
                try:
                    # Extract settings for direct function calls (only for Sonarr)
                    if app_type == "sonarr":
                        api_url = combined_settings.get("api_url", "").strip()
                        api_key = combined_settings.get("api_key", "").strip()
                        api_timeout = combined_settings.get("api_timeout", 120)
                        monitored_only = combined_settings.get("monitored_only", True)
                        skip_series_refresh = combined_settings.get("skip_series_refresh", False)
                        hunt_upgrade_items = combined_settings.get("hunt_upgrade_items", 0)
                        command_wait_delay = combined_settings.get("command_wait_delay", 1)
                        command_wait_attempts = combined_settings.get("command_wait_attempts", 600)
                        
                        processed_upgrades = process_upgrades(
                            api_url=api_url,
                            api_key=api_key,
                            instance_name=instance_name,  # Added the required instance_name parameter
                            api_timeout=api_timeout,
                            monitored_only=monitored_only,
                            skip_series_refresh=skip_series_refresh,
                            hunt_upgrade_items=hunt_upgrade_items,
                            command_wait_delay=command_wait_delay,
                            command_wait_attempts=command_wait_attempts,
                            stop_check=stop_check_func
                        )
                    else:
                        # For other apps that still use the old signature
                        processed_upgrades = process_upgrades(app_settings=combined_settings, stop_check=stop_check_func)
                    
                    if processed_upgrades:
                        processed_any_items = True
                except Exception as e:
                    app_logger.error(f"Error during upgrade processing for {instance_name}: {e}", exc_info=True)

            # Small delay between instances if needed (optional)
            if not stop_event.is_set():
                 time.sleep(1) # Short pause

            # --- Process Swaparr (stalled downloads) --- #
            try:
                # Try to import Swaparr module
                if not 'process_stalled_downloads' in locals():
                    try:
                        # Import directly from handler module to avoid circular imports
                        from src.primary.apps.swaparr.handler import process_stalled_downloads
                        swaparr_logger = get_logger("swaparr")
                        swaparr_logger.debug(f"Successfully imported Swaparr module")
                    except (ImportError, AttributeError) as e:
                        app_logger.debug(f"Swaparr module not available or missing functions: {e}")
                        process_stalled_downloads = None
                
                # Check if Swaparr is enabled
                swaparr_settings = settings_manager.load_settings("swaparr")
                if swaparr_settings and swaparr_settings.get("enabled", False) and process_stalled_downloads:
                    app_logger.info(f"Running Swaparr on {app_type} instance: {instance_name}")
                    process_stalled_downloads(app_type, combined_settings, swaparr_settings)
                    app_logger.info(f"Completed Swaparr processing for {app_type} instance: {instance_name}")
            except Exception as e:
                app_logger.error(f"Error during Swaparr processing for {instance_name}: {e}", exc_info=True)

        # --- Cycle End & Sleep --- #
        calculate_reset_time(app_type) # Pass app_type here if needed by the function

        # Log cycle completion
        if processed_any_items:
            app_logger.info(f"=== {app_type.upper()} cycle finished. Processed items across instances. ===")
        else:
            app_logger.info(f"=== {app_type.upper()} cycle finished. No items processed in any instance. ===")
            
        # Calculate sleep duration (use configured or default value)
        sleep_seconds = app_settings.get("sleep_duration", 900)  # Default to 15 minutes
                
        # Sleep with periodic checks for reset file
        app_logger.info(f"Sleeping for {sleep_seconds} seconds before next cycle...")
                
        # Use shorter sleep intervals and check for reset file
        wait_interval = 1  # Check every second to be more responsive
        elapsed = 0
        reset_file_path = f"/config/reset/{app_type}.reset"
                
        while elapsed < sleep_seconds:
            # Check if stop event is set
            if stop_event.is_set():
                app_logger.info("Stop event detected during sleep. Breaking out of sleep cycle.")
                break
                        
            # Check if reset file exists
            if os.path.exists(reset_file_path):
                try:
                    # Read timestamp from the file (if it exists)
                    with open(reset_file_path, 'r') as f:
                        timestamp = f.read().strip()
                    app_logger.info(f"!!! RESET FILE DETECTED !!! Manual cycle reset triggered for {app_type} (timestamp: {timestamp}). Starting new cycle immediately.")
                        
                    # Delete the reset file
                    os.remove(reset_file_path)
                    app_logger.info(f"Reset file removed for {app_type}. Starting new cycle now.")
                    break
                except Exception as e:
                    app_logger.error(f"Error processing reset file for {app_type}: {e}", exc_info=True)
                    # Try to remove the file even if reading failed
                    try:
                        os.remove(reset_file_path)
                    except:
                        pass
                    break
                        
            # Sleep for a short interval
            stop_event.wait(wait_interval)
            elapsed += wait_interval
                    
            # If we've slept for at least 30 seconds, update the logger message every 30 seconds
            if elapsed > 0 and elapsed % 30 == 0:
                app_logger.info(f"Still sleeping, {sleep_seconds - elapsed} seconds remaining before next cycle...")
                
    app_logger.info(f"=== [{app_type.upper()}] Thread stopped ====")

def reset_app_cycle(app_type: str) -> bool:
    """
    Trigger a manual reset of an app's cycle.
    
    Args:
        app_type: The type of Arr application (sonarr, radarr, lidarr, readarr, etc.)
        
    Returns:
        bool: True if the reset was triggered, False if the app is not running
    """
    logger.info(f"Manual cycle reset requested for {app_type} - Creating reset file")
    
    # Create a reset file for this app
    reset_file_path = f"/config/reset/{app_type}.reset"
    try:
        with open(reset_file_path, 'w') as f:
            f.write(str(int(time.time())))
        logger.info(f"Reset file created for {app_type}. Cycle will reset on next check.")
        return True
    except Exception as e:
        logger.error(f"Error creating reset file for {app_type}: {e}", exc_info=True)
        return False

def start_app_threads():
    """Start threads for all configured and enabled apps."""
    configured_apps_list = settings_manager.get_configured_apps() # Corrected function name
    configured_apps = {app: True for app in configured_apps_list} # Convert list to dict format expected below

    for app_type, is_configured in configured_apps.items():
        if is_configured:
            # Optional: Add an explicit 'enabled' setting check if desired
            # enabled = settings_manager.get_setting(app_type, "enabled", True)
            # if not enabled:
            #     logger.info(f"Skipping {app_type} thread as it is disabled in settings.")
            #     continue

            if app_type not in app_threads or not app_threads[app_type].is_alive():
                if app_type in app_threads: # If it existed but died
                    logger.warning(f"{app_type} thread died, restarting...")
                    del app_threads[app_type]
                else: # Starting for the first time
                    logger.info(f"Starting thread for {app_type}...")

                thread = threading.Thread(target=app_specific_loop, args=(app_type,), name=f"{app_type}-Loop", daemon=True)
                app_threads[app_type] = thread
                thread.start()
        elif app_type in app_threads and app_threads[app_type].is_alive():
             # If app becomes un-configured, stop its thread? Or let it fail connection check?
             # For now, let it run and fail connection check.
             logger.warning(f"{app_type} is no longer configured. Thread will likely stop after failing connection checks.")
        # else: # App not configured and no thread running - do nothing
            # logger.debug(f"{app_type} is not configured. No thread started.")
        pass # Corrected indentation

def check_and_restart_threads():
    """Check if any threads have died and restart them if the app is still configured."""
    configured_apps_list = settings_manager.get_configured_apps() # Corrected function name
    configured_apps = {app: True for app in configured_apps_list} # Convert list to dict format expected below

    for app_type, thread in list(app_threads.items()):
        if not thread.is_alive():
            logger.warning(f"{app_type} thread died unexpectedly.")
            del app_threads[app_type] # Remove dead thread
            # Only restart if it's still configured
            if configured_apps.get(app_type, False):
                logger.info(f"Restarting thread for {app_type}...")
                new_thread = threading.Thread(target=app_specific_loop, args=(app_type,), name=f"{app_type}-Loop", daemon=True)
                app_threads[app_type] = new_thread
                new_thread.start()
            else:
                logger.info(f"Not restarting {app_type} thread as it is no longer configured.")

def shutdown_handler(signum, frame):
    """Handle termination signals (SIGINT, SIGTERM)."""
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    stop_event.set() # Signal all threads to stop

def shutdown_threads():
    """Wait for all threads to finish."""
    logger.info("Waiting for app threads to finish...")
    active_thread_list = list(app_threads.values())
    for thread in active_thread_list:
        thread.join(timeout=15) # Wait up to 15 seconds per thread
        if thread.is_alive():
            logger.warning(f"Thread {thread.name} did not stop gracefully.")
    logger.info("All app threads stopped.")

def process_radarr_hunting(manager, hunting_manager_stop_event):
    """
    Process Radarr-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.radarr import get_configured_instances
        from src.primary.apps.radarr.api import get_movie_by_id, get_movie_file, get_download_queue
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Radarr is configured
        radarr_config = APP_CONFIG.get("radarr")
        if not radarr_config:
            logger.error("[HUNTING] No configuration found for Radarr, cannot process hunting")
            return
        
        # Get all configured Radarr instances
        radarr_instances = get_configured_instances()
        
        for instance in radarr_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("radarr", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("radarr", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_movie_by_id": lambda id: get_movie_by_id(api_url, api_key, id, api_timeout),
                "get_movie_file": lambda id: get_movie_file(api_url, api_key, id, api_timeout),
                "get_download_queue": lambda: get_download_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all movies to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_download_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each movie ID
            processed_count = 0
            for movie_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing movie ID: {movie_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    primary_data, file_data, _ = fetch_api_data_for_item("radarr", movie_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for movie ID {movie_id}, skipping")
                        continue
                    
                    # Log basic details
                    title = primary_data.get('title', 'Unknown')
                    year = primary_data.get('year', 'Unknown')
                    has_file = primary_data.get('hasFile', False)
                    monitored = primary_data.get('monitored', False)
                    
                    logger.info(f"[HUNTING] Movie details - ID: {movie_id}, Title: {title}, "
                               f"Year: {year}, Status: {'Downloaded' if has_file else 'Missing'}, "
                               f"Monitored: {monitored}")
                    
                    # Log file details if available
                    if file_data:
                        quality = get_nested_value(file_data, "quality.quality.name")
                        size_mb = round(file_data.get('size', 0) / (1024 * 1024), 2)
                        logger.info(f"[HUNTING] Movie file - Quality: {quality or 'Unknown'}, Size: {size_mb} MB")
                    
                    # Check if movie is in queue
                    movie_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('movieId') == int(movie_id):
                                movie_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                logger.info(f"[HUNTING] Movie in download queue - ID: {movie_id}, Title: {title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}")
                                break
                    
                    if not movie_in_queue and not has_file and monitored:
                        logger.info(f"[HUNTING] Movie not in download queue and not downloaded - "
                                   f"ID: {movie_id}, Title: {title}, Monitored: {monitored}")
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("radarr", primary_data, queue_data)
                    
                    # Check if this movie is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(movie_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("radarr", instance_name, movie_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for movie ID {movie_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for movie ID {movie_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("radarr", instance_name, movie_id, 
                                                         primary_data, file_data, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = f"{title} ({year})"
                        
                        # Add the entry to history
                        add_history_entry("radarr", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for movie ID {movie_id}: {hunt_status}")
                    
                    # Track movie in memory
                    movie_info = {
                        "id": movie_id,
                        "title": title,
                        "year": year,
                        "status": hunt_status,
                        "instance_name": instance_name
                    }
                    
                    # Add to tracking or update
                    manager.track_movie(movie_id, instance_name, movie_info)
                    logger.info(f"[HUNTING] Movie ID {movie_id} is already tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing movie ID {movie_id}: {e}")
                    continue
            
            logger.info(f"[HUNTING] Processed {processed_count} items for {instance_name}")
        
        logger.info(f"[HUNTING] === Radarr hunting cycle completed ====")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Radarr hunting process: {str(e)}")

def process_sonarr_hunting(manager, hunting_manager_stop_event):
    """
    Process Sonarr-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.sonarr import get_configured_instances
        from src.primary.apps.sonarr.api import get_series_by_id, get_episode, get_queue
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Sonarr is configured
        sonarr_config = APP_CONFIG.get("sonarr")
        if not sonarr_config:
            logger.error("[HUNTING] No configuration found for Sonarr, cannot process hunting")
            return
        
        # Get all configured Sonarr instances
        sonarr_instances = get_configured_instances()
        
        for instance in sonarr_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("sonarr", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("sonarr", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_series_by_id": lambda id: get_series_by_id(api_url, api_key, api_timeout, id),
                "get_episode": lambda id: get_episode(api_url, api_key, api_timeout, id),
                "get_queue": lambda: get_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all series to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each series ID
            processed_count = 0
            for series_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing series ID: {series_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    # Note: Episode data (if needed) would be handled separately as it's multiple items per series
                    primary_data, _, _ = fetch_api_data_for_item("sonarr", series_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for series ID {series_id}, skipping")
                        continue
                    
                    # Log basic details
                    title = primary_data.get('title', 'Unknown')
                    monitored = primary_data.get('monitored', False)
                    status = primary_data.get('status', 'Unknown')
                    
                    # Get statistics if available
                    episode_count = get_nested_value(primary_data, "statistics.episodeCount", 0)
                    episode_file_count = get_nested_value(primary_data, "statistics.episodeFileCount", 0)
                    
                    logger.info(f"[HUNTING] Series details - ID: {series_id}, Title: {title}, "
                               f"Status: {status}, Monitored: {monitored}, "
                               f"Episodes: {episode_count}, Available: {episode_file_count}")
                    
                    # Check if series has episodes in queue
                    series_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('seriesId') == int(series_id):
                                series_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                episode_title = get_nested_value(queue_item, "episode.title", "Unknown Episode")
                                logger.info(f"[HUNTING] Series has episode in download queue - ID: {series_id}, "
                                           f"Title: {title}, Episode: {episode_title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}")
                                break
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("sonarr", primary_data, queue_data)
                    
                    # Check if this series is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(series_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("sonarr", instance_name, series_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for series ID {series_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for series ID {series_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("sonarr", instance_name, series_id, 
                                                         primary_data, None, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = title
                        
                        # Add the entry to history
                        add_history_entry("sonarr", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for series ID {series_id}: {hunt_status}")
                    
                    # Track series in memory
                    series_info = {
                        "id": series_id,
                        "title": title,
                        "status": hunt_status,
                        "instance_name": instance_name
                    }
                    
                    # Add to tracking or update
                    # Note: Using track_movie method for now, could be renamed to track_item in the future for clarity
                    manager.track_movie(series_id, instance_name, series_info)
                    logger.info(f"[HUNTING] Series ID {series_id} is now tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing series ID {series_id}: {e}")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Sonarr hunting process: {e}")
        logger.error(traceback.format_exc())


def process_lidarr_hunting(manager, hunting_manager_stop_event):
    """
    Process Lidarr-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.lidarr import get_configured_instances
        from src.primary.apps.lidarr.api import get_artist_by_id, get_queue, get_album_by_artist_id
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Lidarr is configured
        lidarr_config = APP_CONFIG.get("lidarr")
        if not lidarr_config:
            logger.error("[HUNTING] No configuration found for Lidarr, cannot process hunting")
            return
        
        # Get all configured Lidarr instances
        lidarr_instances = get_configured_instances()
        
        for instance in lidarr_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("lidarr", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("lidarr", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_artist_by_id": lambda id: get_artist_by_id(api_url, api_key, api_timeout, id),
                "get_album_by_artist_id": lambda id: get_album_by_artist_id(api_url, api_key, api_timeout, id),
                "get_queue": lambda: get_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all artists to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each artist ID
            processed_count = 0
            for artist_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing artist ID: {artist_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    primary_data, _, _ = fetch_api_data_for_item("lidarr", artist_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for artist ID {artist_id}, skipping")
                        continue
                    
                    # Log basic details
                    artist_name = primary_data.get('artistName', 'Unknown')
                    monitored = primary_data.get('monitored', False)
                    status = primary_data.get('status', 'Unknown')
                    
                    # Get statistics if available
                    album_count = get_nested_value(primary_data, "statistics.albumCount", 0)
                    track_count = get_nested_value(primary_data, "statistics.trackCount", 0)
                    track_file_count = get_nested_value(primary_data, "statistics.trackFileCount", 0)
                    
                    logger.info(f"[HUNTING] Artist details - ID: {artist_id}, Artist: {artist_name}, "
                               f"Status: {status}, Monitored: {monitored}, "
                               f"Albums: {album_count}, Tracks: {track_count}, Available: {track_file_count}")
                    
                    # Check if artist has albums in queue
                    artist_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('artistId') == int(artist_id):
                                artist_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                album_title = get_nested_value(queue_item, "album.title", "Unknown Album")
                                logger.info(f"[HUNTING] Artist has album in download queue - ID: {artist_id}, "
                                           f"Artist: {artist_name}, Album: {album_title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}")
                                break
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("lidarr", primary_data, queue_data)
                    
                    # Check if this artist is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(artist_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("lidarr", instance_name, artist_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for artist ID {artist_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for artist ID {artist_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("lidarr", instance_name, artist_id, 
                                                         primary_data, None, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = artist_name
                        
                        # Add the entry to history
                        add_history_entry("lidarr", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for artist ID {artist_id}: {hunt_status}")
                    
                    # Track artist in memory
                    artist_info = {
                        "id": artist_id,
                        "title": artist_name,  # Using title key for consistency with other app types
                        "status": hunt_status,
                        "instance_name": instance_name
                    }
                    
                    # Add to tracking or update
                    # Note: Using track_movie method for now, could be renamed to track_item in the future for clarity
                    manager.track_movie(artist_id, instance_name, artist_info)
                    logger.info(f"[HUNTING] Artist ID {artist_id} is now tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing artist ID {artist_id}: {e}")
                    
            logger.info(f"[HUNTING] Processed {processed_count} artists for {instance_name}")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Lidarr hunting process: {e}")
        logger.error(traceback.format_exc())


def process_readarr_hunting(manager, hunting_manager_stop_event):
    """
    Process Readarr-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.readarr import get_configured_instances
        from src.primary.apps.readarr.api import get_author_by_id, get_queue, get_books_by_author_id
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Readarr is configured
        readarr_config = APP_CONFIG.get("readarr")
        if not readarr_config:
            logger.error("[HUNTING] No configuration found for Readarr, cannot process hunting")
            return
        
        # Get all configured Readarr instances
        readarr_instances = get_configured_instances()
        
        for instance in readarr_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("readarr", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("readarr", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_author_by_id": lambda id: get_author_by_id(api_url, api_key, api_timeout, id),
                "get_books_by_author_id": lambda id: get_books_by_author_id(api_url, api_key, api_timeout, id),
                "get_queue": lambda: get_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all authors to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each author ID
            processed_count = 0
            for author_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing author ID: {author_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    primary_data, _, _ = fetch_api_data_for_item("readarr", author_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for author ID {author_id}, skipping")
                        continue
                    
                    # Log basic details
                    author_name = primary_data.get('authorName', 'Unknown')
                    monitored = primary_data.get('monitored', False)
                    status = primary_data.get('status', 'Unknown')
                    
                    # Get statistics if available
                    book_count = get_nested_value(primary_data, "statistics.bookCount", 0)
                    book_file_count = get_nested_value(primary_data, "statistics.bookFileCount", 0)
                    
                    logger.info(f"[HUNTING] Author details - ID: {author_id}, Name: {author_name}, "
                               f"Status: {status}, Monitored: {monitored}, "
                               f"Books: {book_count}, Available: {book_file_count}")
                    
                    # Check if author has books in queue
                    author_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('authorId') == int(author_id):
                                author_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                book_title = get_nested_value(queue_item, "book.title", "Unknown Book")
                                logger.info(f"[HUNTING] Author has book in download queue - ID: {author_id}, "
                                           f"Author: {author_name}, Book: {book_title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}")
                                break
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("readarr", primary_data, queue_data)
                    
                    # Check if this author is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(author_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("readarr", instance_name, author_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for author ID {author_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for author ID {author_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("readarr", instance_name, author_id, 
                                                         primary_data, None, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = author_name
                        
                        # Add the entry to history
                        add_history_entry("readarr", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for author ID {author_id}: {hunt_status}")
                    
                    # Track author in memory
                    author_info = {
                        "id": author_id,
                        "title": author_name,  # Using title key for consistency with other app types
                        "status": hunt_status,
                        "instance_name": instance_name
                    }
                    
                    # Add to tracking or update
                    manager.track_movie(author_id, instance_name, author_info)
                    logger.info(f"[HUNTING] Author ID {author_id} is now tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing author ID {author_id}: {e}")
                    
            logger.info(f"[HUNTING] Processed {processed_count} authors for {instance_name}")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Readarr hunting process: {e}")
        logger.error(traceback.format_exc())


def process_whisparr_hunting(manager, hunting_manager_stop_event):
    """
    Process Whisparr-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.whisparr import get_configured_instances
        from src.primary.apps.whisparr.api import get_movie_by_id, get_movie_file, get_download_queue
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Whisparr is configured
        whisparr_config = APP_CONFIG.get("whisparr")
        if not whisparr_config:
            logger.error("[HUNTING] No configuration found for Whisparr, cannot process hunting")
            return
        
        # Get all configured Whisparr instances
        whisparr_instances = get_configured_instances()
        
        for instance in whisparr_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("whisparr", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("whisparr", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_movie_by_id": lambda id: get_movie_by_id(api_url, api_key, api_timeout, id),
                "get_movie_file": lambda id: get_movie_file(api_url, api_key, api_timeout, id),
                "get_download_queue": lambda: get_download_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all movies to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_download_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each movie ID
            processed_count = 0
            for movie_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing scene ID: {movie_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    primary_data, file_data, _ = fetch_api_data_for_item("whisparr", movie_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for scene ID {movie_id}, skipping")
                        continue
                    
                    # Log basic details
                    title = primary_data.get('title', 'Unknown')
                    has_file = primary_data.get('hasFile', False)
                    monitored = primary_data.get('monitored', False)
                    studio = primary_data.get('studio', 'Unknown')
                    
                    logger.info(f"[HUNTING] Scene details - ID: {movie_id}, Title: {title}, "
                               f"Studio: {studio}, Status: {'Downloaded' if has_file else 'Missing'}, "
                               f"Monitored: {monitored}")
                    
                    # Log file details if available
                    if file_data:
                        quality = get_nested_value(file_data, "quality.quality.name", "Unknown")
                        size_mb = round(file_data.get('size', 0) / (1024 * 1024), 2)
                        logger.info(f"[HUNTING] Scene file - Quality: {quality}, Size: {size_mb} MB")
                    
                    # Check if movie is in queue
                    movie_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('movieId') == int(movie_id):
                                movie_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                logger.info(f"[HUNTING] Scene in download queue - ID: {movie_id}, Title: {title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}")
                                break
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("whisparr", primary_data, queue_data)
                    
                    # Check if this movie is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(movie_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("whisparr", instance_name, movie_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for scene ID {movie_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for scene ID {movie_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("whisparr", instance_name, movie_id, 
                                                         primary_data, file_data, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = title
                        
                        # Add the entry to history
                        add_history_entry("whisparr", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for scene ID {movie_id}: {hunt_status}")
                    
                    # Track movie in memory
                    movie_info = {
                        "id": movie_id,
                        "title": title,
                        "status": hunt_status,
                        "instance_name": instance_name
                    }
                    
                    # Add to tracking or update
                    manager.track_movie(movie_id, instance_name, movie_info)
                    logger.info(f"[HUNTING] Scene ID {movie_id} is now tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing scene ID {movie_id}: {e}")
                    
            logger.info(f"[HUNTING] Processed {processed_count} scenes for {instance_name}")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Whisparr hunting process: {e}")
        logger.error(traceback.format_exc())


def process_eros_hunting(manager, hunting_manager_stop_event):
    """
    Process Eros-specific hunting logic using the unified field handling approach.
    This completely eliminates any translation between API responses and history entries,
    with the field_mapper handling all the JSON structure creation consistently.
    
    Eros uses the WhisparrV3 API structure but with enhanced fields.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Import necessary modules
        from src.primary.apps.eros import get_configured_instances
        from src.primary.apps.eros.api import get_movie_by_id, get_movie_file, get_download_queue
        from src.primary.history_manager import get_history, update_history_entry_status, add_history_entry
        from src.primary.stateful_manager import get_processed_ids
        from src.primary.utils.field_mapper import determine_hunt_status, get_nested_value, APP_CONFIG, create_history_entry, fetch_api_data_for_item
        
        # Check if Eros is configured
        eros_config = APP_CONFIG.get("eros")
        if not eros_config:
            logger.error("[HUNTING] No configuration found for Eros, cannot process hunting")
            return
        
        # Get all configured Eros instances
        eros_instances = get_configured_instances()
        
        for instance in eros_instances:
            # Skip processing if stop event is set
            if hunting_manager_stop_event.is_set():
                return
                
            instance_name = instance.get("instance_name", "Default")
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            api_timeout = settings_manager.get_advanced_setting("api_timeout", 120)
            
            if not api_url or not api_key:
                logger.warning(f"[HUNTING] Missing API URL or key for instance: {instance_name}, skipping")
                continue
                
            logger.info(f"[HUNTING] Checking processed IDs for instance: {instance_name}")
            
            # Load processed IDs from stateful_manager
            processed_ids = get_processed_ids("eros", instance_name)
            logger.info(f"[HUNTING] Found {len(processed_ids)} processed IDs for instance {instance_name}")
            
            # Load history entries to check for existing entries
            history_data = get_history("eros", instance_name)
            
            # Create a dictionary of API handlers for easier access
            api_handlers = {
                "get_movie_by_id": lambda id: get_movie_by_id(api_url, api_key, api_timeout, id),
                "get_movie_file": lambda id: get_movie_file(api_url, api_key, api_timeout, id),
                "get_download_queue": lambda: get_download_queue(api_url, api_key, api_timeout)
            }
            
            # Get queue data once for all movies to avoid multiple API calls
            queue_data = None
            try:
                queue_data = api_handlers["get_download_queue"]()
                logger.info(f"[HUNTING] Current download queue has {len(queue_data)} items for instance {instance_name}")
            except Exception as e:
                logger.error(f"[HUNTING] Error fetching download queue for {instance_name}: {e}")
                queue_data = []
            
            # Process each movie ID
            processed_count = 0
            for movie_id in processed_ids:
                # Skip processing if stop event is set
                if hunting_manager_stop_event.is_set():
                    return
                    
                processed_count += 1
                logger.info(f"[HUNTING] Processing scene ID: {movie_id} ({processed_count}/{len(processed_ids)}) for instance {instance_name}")
                
                try:
                    # Use the unified field handler to fetch all needed data
                    primary_data, file_data, _ = fetch_api_data_for_item("eros", movie_id, api_handlers)
                    
                    if not primary_data:
                        logger.warning(f"[HUNTING] No data returned from API for scene ID {movie_id}, skipping")
                        continue
                    
                    # Log basic details
                    title = primary_data.get('title', 'Unknown')
                    has_file = primary_data.get('hasFile', False)
                    monitored = primary_data.get('monitored', False)
                    studio = primary_data.get('studio', 'Unknown')
                    
                    # Get collection info if available
                    collection = primary_data.get('collection', {})
                    collection_name = collection.get('name', 'None') if collection else 'None'
                    
                    logger.info(f"[HUNTING] Scene details - ID: {movie_id}, Title: {title}, "
                               f"Studio: {studio}, Collection: {collection_name}, "
                               f"Status: {'Downloaded' if has_file else 'Missing'}, "
                               f"Monitored: {monitored}")
                    
                    # Log file details if available
                    if file_data:
                        quality = get_nested_value(file_data, "quality.quality.name", "Unknown")
                        size_mb = round(file_data.get('size', 0) / (1024 * 1024), 2)
                        resolution = file_data.get('resolution', 'Unknown')
                        logger.info(f"[HUNTING] Scene file - Quality: {quality}, Resolution: {resolution}, Size: {size_mb} MB")
                    
                    # Check if movie is in queue
                    movie_in_queue = False
                    queue_item_data = None
                    if queue_data:
                        for queue_item in queue_data:
                            if queue_item.get('movieId') == int(movie_id):
                                movie_in_queue = True
                                queue_item_data = queue_item
                                progress = queue_item.get('progress', 0)
                                status = queue_item.get('status', 'Unknown')
                                protocol = queue_item.get('protocol', 'Unknown')
                                size_mb = round(queue_item.get('size', 0) / (1024 * 1024), 2) if queue_item.get('size') else 0
                                remaining_mb = round(queue_item.get('sizeleft', 0) / (1024 * 1024), 2) if queue_item.get('sizeleft') else 0
                                logger.info(f"[HUNTING] Scene in download queue - ID: {movie_id}, Title: {title}, "
                                           f"Progress: {progress}%, Status: {status}, Protocol: {protocol}, "
                                           f"Size: {size_mb} MB, Remaining: {remaining_mb} MB")
                                break
                    
                    # Determine hunt status
                    hunt_status = determine_hunt_status("eros", primary_data, queue_data)
                    
                    # Check if this movie is already in history
                    existing_entry = None
                    if history_data.get("entries"):
                        existing_entry = next((entry for entry in history_data["entries"] 
                                              if str(entry.get("id", "")) == str(movie_id)), None)
                    
                    # Update or create history entry
                    if existing_entry:
                        # Just update the status if it exists
                        update_history_entry_status("eros", instance_name, movie_id, hunt_status)
                        
                        # Log status changes
                        previous_status = existing_entry.get("hunt_status", "Not Tracked")
                        if previous_status != hunt_status:
                            logger.info(f"[HUNTING] Updating status for scene ID {movie_id} from '{previous_status}' to '{hunt_status}'")
                        else:
                            logger.info(f"[HUNTING] Status unchanged for scene ID {movie_id}: '{hunt_status}'")
                    else:
                        # Create a new history entry with the unified approach
                        entry_data = create_history_entry("eros", instance_name, movie_id, 
                                                         primary_data, file_data, queue_data)
                        
                        # Add required name field for history_manager
                        entry_data["name"] = title
                        
                        # Add the entry to history
                        add_history_entry("eros", entry_data)
                        logger.info(f"[HUNTING] Created new history entry for scene ID {movie_id}: {hunt_status}")
                    
                    # Track movie in memory
                    movie_info = {
                        "id": movie_id,
                        "title": title,
                        "status": hunt_status,
                        "instance_name": instance_name,
                        "studio": studio
                    }
                    
                    # Add to tracking or update
                    manager.track_movie(movie_id, instance_name, movie_info)
                    logger.info(f"[HUNTING] Scene ID {movie_id} is now tracked for instance {instance_name}, status: {hunt_status}")
                    
                except Exception as e:
                    logger.error(f"[HUNTING] Error processing scene ID {movie_id}: {e}")
                    
            logger.info(f"[HUNTING] Processed {processed_count} scenes for {instance_name}")
    except Exception as e:
        logger.error(f"[HUNTING] Error in Eros hunting process: {e}")
        logger.error(traceback.format_exc())


def process_whisparrv2_hunting(manager, hunting_manager_stop_event):
    """
    Process WhisparrV2-specific hunting logic using the unified field handling approach.
    This function is included for completeness, but it is recommended to use the Eros handler
    for Whisparr V2, as it uses the V3 API.
    
    Args:
        manager: The HuntingManager instance
        hunting_manager_stop_event: Event to check if hunting should stop
    """
    logger = get_logger("hunting")
    
    try:
        # Simply redirect to Eros processing as recommended approach
        logger.info("[HUNTING] WhisparrV2 hunting redirected to Eros implementation since they share API structure")
        process_eros_hunting(manager, hunting_manager_stop_event)
    except Exception as e:
        logger.error(f"[HUNTING] Error in WhisparrV2 hunting process: {e}")
        logger.error(traceback.format_exc())

def hunting_manager_loop():
    """
    Main hunting manager loop that coordinates hunting across different app types.
    Currently focuses on Radarr but structured to allow easy addition of other apps.
    """
    logger = get_logger("hunting")
    logger.info("[HUNTING] Hunting Manager background thread started.")
    manager = HuntingManager("/config")
    logger.info("[HUNTING] Hunting Manager is Ready to Hunt!")

    # On first run, log all existing tracked items (prior history)
    for app_name in os.listdir(manager.hunting_dir):
        app_path = os.path.join(manager.hunting_dir, app_name)
        if not os.path.isdir(app_path):
            continue
        for instance_file in os.listdir(app_path):
            if not instance_file.endswith('.json'):
                continue
            instance_path = os.path.join(app_path, instance_file)
            with open(instance_path, 'r') as f:
                tracking_data = json.load(f)
            for item in tracking_data.get("tracking", {}).get("items", []):
                logger.info(f"[HUNTING] Prior tracked: {item['name']} (ID: {item['id']}) - Status: {item['status']} - Requested: {item['requested_at']}")

    while not hunting_manager_stop_event.is_set():
        logger.info("[HUNTING] === Hunting Manager cycle started ===")
        
        # Process Radarr hunting
        process_radarr_hunting(manager, hunting_manager_stop_event)
        
        # In the future, add other app-specific hunting functions here
        process_sonarr_hunting(manager, hunting_manager_stop_event)
        process_lidarr_hunting(manager, hunting_manager_stop_event)
        process_readarr_hunting(manager, hunting_manager_stop_event)
        process_whisparr_hunting(manager, hunting_manager_stop_event)
        process_eros_hunting(manager, hunting_manager_stop_event)
        process_whisparrv2_hunting(manager, hunting_manager_stop_event)
        # process_lidarr_hunting(manager, hunting_manager_stop_event)
        # process_readarr_hunting(manager, hunting_manager_stop_event)
        # process_whisparr_hunting(manager, hunting_manager_stop_event)
        
        logger.info("[HUNTING] === Hunting Manager cycle ended ===")
        hunting_manager_stop_event.wait(30)  # Check every 30 seconds
    
    logger.info("[HUNTING] Hunting Manager background thread stopped.")

def start_huntarr():
    """Main entry point for Huntarr background tasks."""
    logger.info(f"--- Starting Huntarr Background Tasks v{__version__} --- ")

    # Start the Hunting Manager thread
    global hunting_manager_thread
    if hunting_manager_thread is None or not hunting_manager_thread.is_alive():
        logger.info("[HUNTING] Starting Hunting Manager background thread...")
        hunting_manager_thread = threading.Thread(target=hunting_manager_loop, name="HuntingManager-Loop", daemon=True)
        hunting_manager_thread.start()

    # Perform initial settings migration if specified (e.g., via env var or arg)
    if os.environ.get("HUNTARR_RUN_MIGRATION", "false").lower() == "true":
        logger.info("Running settings migration from huntarr.json (if found)...")
        settings_manager.migrate_from_huntarr_json()

    # Log initial configuration for all known apps
    for app_name in settings_manager.KNOWN_APP_TYPES: # Corrected attribute name
        try:
            config.log_configuration(app_name)
        except Exception as e:
            logger.error(f"Error logging initial configuration for {app_name}: {e}")

    try:
        # Main loop: Start and monitor app threads
        while not stop_event.is_set():
            start_app_threads() # Start/Restart threads for configured apps
            # check_and_restart_threads() # This is implicitly handled by start_app_threads checking is_alive
            stop_event.wait(15) # Check for stop signal every 15 seconds

    except Exception as e:
        logger.exception(f"Unexpected error in main monitoring loop: {e}")
    finally:
        logger.info("Background task main loop exited. Shutting down threads...")
        if not stop_event.is_set():
             stop_event.set() # Ensure stop is signaled if loop exited unexpectedly
        shutdown_threads()
        logger.info("--- Huntarr Background Tasks stopped --- ")