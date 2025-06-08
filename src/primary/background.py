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
import datetime
import traceback
import pytz

# Define the version number
__version__ = "1.0.0" # Consider updating this based on changes

# Set up logging first
from src.primary.utils.logger import setup_main_logger, get_logger # Import get_logger
logger = setup_main_logger()
hunting_logger = get_logger("hunting")  # Add hunting logger for Hunt Manager logs

# Import necessary modules
from src.primary import config, settings_manager
# Removed keys_manager import as settings_manager handles API details
from src.primary.state import check_state_reset, calculate_reset_time
from src.primary.stats_manager import check_hourly_cap_exceeded
# Instance list generator has been removed
from src.primary.scheduler_engine import start_scheduler, stop_scheduler
from src.primary.migrate_configs import migrate_json_configs  # Import the migration function
# from src.primary.utils.app_utils import get_ip_address # No longer used here

# Global state for managing app threads and their status
app_threads: Dict[str, threading.Thread] = {}
stop_event = threading.Event() # Use an event for clearer stop signaling

# Hourly cap scheduler thread
hourly_cap_scheduler_thread = None

# Instance list generator has been removed

def _get_user_timezone():
    """Get the user's selected timezone from general settings"""
    try:
        from src.primary.utils.timezone_utils import get_user_timezone
        return get_user_timezone()
    except Exception:
        return pytz.UTC

def app_specific_loop(app_type: str) -> None:
    """
    Main processing loop for a specific Arr application.

    Args:
        app_type: The type of Arr application (sonarr, radarr, lidarr, readarr)
    """
    from src.primary.cycle_tracker import update_next_cycle
    
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

        # Mark cycle as started (set cyclelock to True)
        try:
            from src.primary.cycle_tracker import start_cycle
            start_cycle(app_type)
        except Exception as e:
            app_logger.warning(f"Failed to mark cycle start for {app_type}: {e}")
            # Non-critical, continue execution

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
        enabled_instances = []
        
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
                
            # --- API Cap Check --- #
            try:
                # Check if hourly API cap is exceeded
                if check_hourly_cap_exceeded(app_type):
                    # Get the current cap status for logging
                    from src.primary.stats_manager import get_hourly_cap_status
                    cap_status = get_hourly_cap_status(app_type)
                    app_logger.info(f"{app_type.upper()} hourly cap reached {cap_status['current_usage']} of {cap_status['limit']} (app-specific limit). Skipping cycle!")
                    continue # Skip this instance if API cap is exceeded
            except Exception as e:
                app_logger.error(f"Error checking hourly API cap for {app_type}: {e}", exc_info=True)
                # Continue with the cycle even if cap check fails - safer than skipping

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
                        hunt_upgrade_items = combined_settings.get("hunt_upgrade_items", 0)
                        upgrade_mode = combined_settings.get("upgrade_mode", "episodes")
                        command_wait_delay = combined_settings.get("command_wait_delay", 1)
                        command_wait_attempts = combined_settings.get("command_wait_attempts", 600)
                        
                        processed_upgrades = process_upgrades(
                            api_url=api_url,
                            api_key=api_key,
                            instance_name=instance_name,  # Added the required instance_name parameter
                            api_timeout=api_timeout,
                            monitored_only=monitored_only,
                            hunt_upgrade_items=hunt_upgrade_items,
                            upgrade_mode=upgrade_mode,
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

            # --- Process Swaparr (stalled downloads) --- #
            try:
                # Try to import Swaparr module
                from src.primary.apps.swaparr.handler import process_stalled_downloads
                from src.primary.settings_manager import load_settings as swaparr_load_settings
                
                # Check if Swaparr is enabled
                swaparr_settings = swaparr_load_settings("swaparr")
                if swaparr_settings and swaparr_settings.get("enabled", False):
                    app_logger.info(f"Running Swaparr stalled download detection on {app_type} instance: {instance_name}")
                    process_stalled_downloads(app_type, combined_settings, swaparr_settings)
                    app_logger.info(f"Completed Swaparr processing for {app_type} instance: {instance_name}")
                else:
                    app_logger.debug(f"Swaparr is disabled, skipping stalled download processing for {app_type} instance: {instance_name}")
            except ImportError as e:
                app_logger.debug(f"Swaparr module not available for {instance_name}: {e}")
            except Exception as e:
                app_logger.error(f"Error during Swaparr processing for {instance_name}: {e}", exc_info=True)

            # Small delay between instances if needed (optional)
            if not stop_event.is_set():
                 time.sleep(1) # Short pause
            enabled_instances.append(instance_name)

        # --- Cycle End & Sleep --- #
        calculate_reset_time(app_type) # Pass app_type here if needed by the function

        # Log cycle completion
        if processed_any_items:
            app_logger.info(f"=== {app_type.upper()} cycle finished. Processed items across instances. ===")
        else:
            app_logger.info(f"=== {app_type.upper()} cycle finished. No items processed in any instance. ===")
            
        # Add state management summary logging for user clarity
        try:
            from src.primary.stateful_manager import get_state_management_summary
            
            # Get total summary across all instances
            total_processed = 0
            has_any_processed = False
            
            for instance_name in enabled_instances:
                summary = get_state_management_summary(app_type, instance_name)
                if summary["has_processed_items"]:
                    total_processed += summary["processed_count"]
                    has_any_processed = True
            
            # Log state management info based on processing results
            if not processed_any_items and has_any_processed:
                # Items were skipped due to state management
                reset_time = get_state_management_summary(app_type, enabled_instances[0])["next_reset_time"] if enabled_instances else None
                if reset_time:
                    app_logger.info(f"STATE MANAGEMENT: {total_processed} items already processed and will not be reprocessed until state reset at {reset_time}.")
                else:
                    app_logger.info(f"STATE MANAGEMENT: {total_processed} items already processed and will not be reprocessed until state management reset.")
            elif processed_any_items:
                # Items were processed, show summary
                reset_time = get_state_management_summary(app_type, enabled_instances[0])['next_reset_time'] if enabled_instances else 'Unknown'
                app_logger.info(f"STATE MANAGEMENT: Total items tracked: {total_processed}. Next state reset: {reset_time}.")
            else:
                # No items processed and no state management blocking
                app_logger.info(f"STATE MANAGEMENT: No items found to process. Items tracked: {total_processed}.")
                
        except Exception as e:
            app_logger.warning(f"Could not generate state management summary: {e}")
            
        # Calculate sleep duration (use configured or default value)
        sleep_seconds = app_settings.get("sleep_duration", 900)  # Default to 15 minutes
                
        # Sleep with periodic checks for reset file
        # Calculate and format the time when the next cycle will begin
        # Use user's selected timezone for all time operations
        
        # Get user's selected timezone
        user_tz = _get_user_timezone()
        
        # Get current time in user's timezone - remove microseconds for clean timestamps
        now_user_tz = datetime.datetime.now(user_tz).replace(microsecond=0)
        
        # Calculate next cycle time in user's timezone without microseconds
        next_cycle_time = now_user_tz + datetime.timedelta(seconds=sleep_seconds)
        
        app_logger.debug(f"Current time ({user_tz}): {now_user_tz.strftime('%Y-%m-%d %H:%M:%S')}")
        app_logger.info(f"Next cycle will begin at {next_cycle_time.strftime('%Y-%m-%d %H:%M:%S')} ({user_tz})")
        app_logger.info(f"Sleep duration: {sleep_seconds} seconds")
        
        # Update cycle tracking with user timezone time
        next_cycle_naive = next_cycle_time.replace(tzinfo=None) if next_cycle_time.tzinfo else next_cycle_time
        update_next_cycle(app_type, next_cycle_naive)
        
        # Mark cycle as ended (set cyclelock to False) and update next cycle time
        # Use user's timezone for internal storage consistency
        try:
            from src.primary.cycle_tracker import end_cycle
            # Convert timezone-aware datetime to naive for clean timestamp generation
            next_cycle_naive = next_cycle_time.replace(tzinfo=None) if next_cycle_time.tzinfo else next_cycle_time
            end_cycle(app_type, next_cycle_naive)
        except Exception as e:
            app_logger.warning(f"Failed to mark cycle end for {app_type}: {e}")
            # Non-critical, continue execution
        
        app_logger.debug(f"Sleeping for {sleep_seconds} seconds before next cycle...")
                
        # Use shorter sleep intervals and check for reset file
        wait_interval = 1  # Check every second to be more responsive
        elapsed = 0
        # Use cross-platform path for reset file
        from src.primary.utils.config_paths import get_reset_path
        reset_file_path = get_reset_path(app_type)
                
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
                app_logger.debug(f"Still sleeping, {sleep_seconds - elapsed} seconds remaining before next cycle...")
                
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
    
    # Create a reset file for this app using cross-platform paths
    from src.primary.utils.config_paths import get_reset_path
    
    reset_file_path = get_reset_path(app_type)
    try:
        # Ensure directory exists
        reset_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to the reset file
        with open(reset_file_path, 'w') as f:
            f.write(str(int(time.time())))
        logger.info(f"Reset file created for {app_type} at {reset_file_path}. Cycle will reset on next check.")
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
    logger.info("Waiting for all app threads to stop...")
    
    # Stop the hourly API cap scheduler
    global hourly_cap_scheduler_thread
    if hourly_cap_scheduler_thread and hourly_cap_scheduler_thread.is_alive():
        # The thread should exit naturally due to the stop_event being set
        logger.info("Waiting for hourly API cap scheduler to stop...")
        hourly_cap_scheduler_thread.join(timeout=5.0)
        if hourly_cap_scheduler_thread.is_alive():
            logger.warning("Hourly API cap scheduler did not stop gracefully")
        else:
            logger.info("Hourly API cap scheduler stopped")
    
    # Stop the scheduler engine
    try:
        logger.info("Stopping schedule action engine...")
        stop_scheduler()
        logger.info("Schedule action engine stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping schedule action engine: {e}")
    
    # Wait for all threads to terminate
    for thread in app_threads.values():
        if thread.is_alive():
            thread.join(timeout=10.0)
    
    logger.info("All app threads stopped.")

def hourly_cap_scheduler_loop():
    """Main loop for the hourly API cap scheduler thread
    Checks time every 30 seconds and resets caps if needed at the top of the hour
    """
    logger.info("Starting hourly API cap scheduler loop")
    
    try:
        from src.primary.stats_manager import reset_hourly_caps
        
        # Initial check in case we're starting right at the top of an hour
        current_time = datetime.datetime.now()
        if current_time.minute == 0:
            logger.info(f"Initial hourly reset triggered at {current_time.hour}:00")
            reset_hourly_caps()
        
        # Main monitoring loop
        while not stop_event.is_set():
            try:
                # Sleep for 30 seconds between checks
                # This ensures we won't miss the top of the hour
                stop_event.wait(30)
                
                if stop_event.is_set():
                    break
                    
                # Check if it's the top of the hour (00 minute mark)
                current_time = datetime.datetime.now()
                if current_time.minute == 0:
                    logger.info(f"Hourly reset triggered at {current_time.hour}:00")
                    success = reset_hourly_caps()
                    if success:
                        logger.info(f"Successfully reset hourly API caps at {current_time.hour}:00")
                    else:
                        logger.error(f"Failed to reset hourly API caps at {current_time.hour}:00")
                
            except Exception as e:
                logger.error(f"Error in hourly cap scheduler: {e}")
                logger.error(traceback.format_exc())
                # Sleep briefly to avoid spinning in case of repeated errors
                time.sleep(5)
                
    except Exception as e:
        logger.error(f"Fatal error in hourly cap scheduler: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Hourly API cap scheduler stopped")

# The instance list generator loop has been removed as it's no longer needed

# The start_instance_list_generator function has been removed as it's no longer needed

def start_hourly_cap_scheduler():
    """Start the hourly API cap scheduler thread"""
    global hourly_cap_scheduler_thread
    
    if hourly_cap_scheduler_thread and hourly_cap_scheduler_thread.is_alive():
        logger.info("Hourly API cap scheduler already running")
        return
    
    # Create and start the scheduler thread
    hourly_cap_scheduler_thread = threading.Thread(
        target=hourly_cap_scheduler_loop, 
        name="HourlyCapScheduler", 
        daemon=True
    )
    hourly_cap_scheduler_thread.start()
    
    logger.info(f"Hourly API cap scheduler started. Thread is alive: {hourly_cap_scheduler_thread.is_alive()}")

def start_huntarr():
    """Main entry point for Huntarr background tasks."""
    logger.info(f"--- Starting Huntarr Background Tasks v{__version__} --- ")
    
    # Run JSON configuration file migration
    try:
        logger.info("Checking for legacy JSON configuration files to migrate...")
        migrate_json_configs()
    except Exception as e:
        logger.error(f"Error during configuration migration: {e}")
        logger.debug(traceback.format_exc())
    
    # Perform initial settings migration if specified (e.g., via env var or arg)
    if os.environ.get("HUNTARR_RUN_MIGRATION", "false").lower() == "true":
        logger.info("Running settings migration from huntarr.json (if found)...")
        settings_manager.migrate_from_huntarr_json()
        
    # Start the hourly API cap scheduler
    try:
        start_hourly_cap_scheduler()
        logger.info("Hourly API cap scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start hourly API cap scheduler: {e}")
        
    # Start the scheduler engine
    try:
        start_scheduler()
        logger.info("Schedule action engine started successfully")
    except Exception as e:
        logger.error(f"Failed to start schedule action engine: {e}")
        
    # Start the discovery tracker for hunt management
    try:
        from src.primary.discovery_tracker import run_discovery_tracker_background
        run_discovery_tracker_background()
        hunting_logger.info("Hunt Manager (discovery tracker) started successfully")
    except Exception as e:
        hunting_logger.error(f"Failed to start Hunt Manager (discovery tracker): {e}")
        
    # Instance list generator has been removed
    logger.debug("Instance list generator has been removed and is no longer needed")

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