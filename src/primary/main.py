#!/usr/bin/env python3
"""
Huntarr - Main entry point for the application
Supports multiple Arr applications running concurrently
"""

import time
import sys
import os
import socket
import signal
import importlib
import logging
import threading
from typing import Dict, List, Optional

# Define the version number
__version__ = "1.0.0"

# Set up logging first to avoid circular imports
from src.primary.utils.logger import setup_logger
logger = setup_logger()

# Now import the rest of the modules
# Import config module itself
from src.primary import config
# Import specific items needed directly
from src.primary.config import SLEEP_DURATION, MINIMUM_DOWNLOAD_QUEUE_SIZE
from src.primary.state import check_state_reset, calculate_reset_time
from src.primary.utils.app_utils import get_ip_address
from src.primary import keys_manager

# Flags to indicate if cycles should restart for each app
restart_cycles = {
    "sonarr": False,
    "radarr": False,
    "lidarr": False,
    "readarr": False
}

# Track active threads
app_threads: Dict[str, threading.Thread] = {}
stop_threads = False

def signal_handler(signum, frame):
    """Handle signals from the web UI for cycle restart"""
    if signum == signal.SIGUSR1:
        # Extract the app type from the signal data if available
        app_type = os.environ.get("RESTART_APP_TYPE", "sonarr")
        logger.info(f"🔄 Received restart signal for {app_type}")
        restart_cycles[app_type] = True

# Register signal handler for SIGUSR1
signal.signal(signal.SIGUSR1, signal_handler)

def force_reload_all_modules():
    """Force reload of all relevant modules to ensure fresh settings"""
    try:
        # Reload config first
        importlib.reload(sys.modules['src.primary.config'])
        logger.debug("Reloaded src.primary.config module")
        # Reload other potentially affected modules if necessary
        # importlib.reload(sys.modules['src.primary.api'])
        # importlib.reload(sys.modules['src.primary.state'])
        # importlib.reload(sys.modules['src.primary.apps.sonarr.missing']) # etc.
    except (KeyError, ImportError, AttributeError) as e:
        logger.error(f"Error reloading modules: {e}")

def check_restart(app_type: str, app_logger: logging.Logger) -> bool:
    """Checks if a restart is flagged for the app type and logs a warning."""
    if restart_cycles[app_type]:
        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
        return True
    return False

def app_specific_loop(app_type: str) -> None:
    """
    Main processing loop for a specific Arr application

    Args:
        app_type: The type of Arr application (sonarr, radarr, lidarr, readarr)
    """
    global restart_cycles

    # Get app-specific logger
    from src.primary.utils.logger import get_logger
    app_logger = get_logger(app_type)

    app_logger.info(f"=== Huntarr starting component for {app_type.title()} interaction ===")

    # server_ip = get_ip_address() # Removed redundant logging of web interface URL
    # app_logger.info(f"Web interface available at http://{server_ip}:9705")

    # Import necessary modules based on app type
    process_missing = None
    process_upgrades = None
    get_queue_size = lambda: 0 # Default to 0

    if app_type == "sonarr":
        from src.primary.apps.sonarr.missing import process_missing_episodes
        from src.primary.apps.sonarr.upgrade import process_cutoff_upgrades
        from src.primary.apps.sonarr.api import get_download_queue_size as get_queue_size
        process_missing = process_missing_episodes
        process_upgrades = process_cutoff_upgrades
        hunt_missing_setting = "hunt_missing_shows"
        hunt_upgrade_setting = "hunt_upgrade_episodes"
    elif app_type == "radarr":
        from src.primary.apps.radarr.missing import process_missing_movies
        from src.primary.apps.radarr.upgrade import process_cutoff_upgrades
        from src.primary.apps.radarr.api import get_download_queue_size as get_queue_size
        process_missing = process_missing_movies
        process_upgrades = process_cutoff_upgrades
        hunt_missing_setting = "hunt_missing_movies"
        hunt_upgrade_setting = "hunt_upgrade_movies"
    elif app_type == "lidarr":
        from src.primary.apps.lidarr.missing import process_missing_albums
        from src.primary.apps.lidarr.upgrade import process_cutoff_upgrades
        from src.primary.apps.lidarr.api import get_download_queue_size as get_queue_size
        process_missing = process_missing_albums
        process_upgrades = process_cutoff_upgrades
        hunt_missing_setting = "hunt_missing_albums"
        hunt_upgrade_setting = "hunt_upgrade_tracks"
    elif app_type == "readarr":
        from src.primary.apps.readarr.missing import process_missing_books
        from src.primary.apps.readarr.upgrade import process_cutoff_upgrades
        # Placeholder for Readarr-specific API functions
        # from src.primary.apps.readarr.api import get_download_queue_size as get_queue_size
        process_missing = process_missing_books
        process_upgrades = process_cutoff_upgrades
        hunt_missing_setting = "hunt_missing_books"
        hunt_upgrade_setting = "hunt_upgrade_books"

    # Get API keys for this app
    api_url, api_key = keys_manager.get_api_keys(app_type)

    # Set the API credentials for this thread context (if needed by API functions)
    # os.environ[f"{app_type.upper()}_API_URL"] = api_url
    # os.environ[f"{app_type.upper()}_API_KEY"] = api_key

    while not stop_threads:
        restart_cycles[app_type] = False

        # Always reload settings from huntarr.json at the start of each cycle
        # Use the config module's refresh_settings
        config.refresh_settings(app_type)

        check_state_reset(app_type)

        app_logger.info(f"=== Starting Huntarr {app_type} cycle ===")

        # Import check_connection dynamically or have a central dispatcher
        try:
            import_module = importlib.import_module(f'src.primary.apps.{app_type}.api')
            check_connection = getattr(import_module, 'check_connection')
        except (ImportError, AttributeError):
            app_logger.error(f"Could not find check_connection function for {app_type}. Skipping connection check.")
            # Decide how to handle this - maybe skip the cycle?
            time.sleep(config.SLEEP_DURATION) # Use config directly
            continue

        # Override the global APP_TYPE for this thread's context if needed by shared modules
        # This might be risky if not managed carefully. Prefer passing app_type explicitly.
        # os.environ["APP_TYPE"] = app_type

        api_connected = False
        connection_attempts = 0
        while not api_connected and not restart_cycles[app_type] and not stop_threads:
            # Reload settings before checking connection in case they changed
            config.refresh_settings(app_type)

            api_connected = check_connection() # Call the app-specific check_connection
            if not api_connected:
                app_logger.error(f"Cannot connect to {app_type.title()}. Please check your API URL and API key.")
                app_logger.info(f"Will retry in 10 seconds...")

                for _ in range(10):
                    time.sleep(1)
                    if check_restart(app_type, app_logger) or stop_threads:
                        break
                if restart_cycles[app_type] or stop_threads: break # Break outer loop too

                connection_attempts += 1
                if connection_attempts >= 3:
                    app_logger.warning(f"Multiple failed connection attempts to {app_type.title()}. Will try again next cycle.")
                    break # Break connection attempt loop

            if check_restart(app_type, app_logger):
                break # Break connection attempt loop to restart cycle

        if not api_connected:
            app_logger.error(f"Connection to {app_type} failed, skipping this cycle.")
            # Use config directly for sleep duration
            sleep_duration = config.SLEEP_DURATION
            sleep_start = time.time()
            sleep_end = sleep_start + sleep_duration
            while time.time() < sleep_end and not check_restart(app_type, app_logger) and not stop_threads:
                 time.sleep(min(1, sleep_end - time.time()))
            continue # Go to next main loop iteration

        processing_done = False

        # Get download queue size
        try:
            download_queue_size = get_queue_size()
            min_download_queue_size = config.MINIMUM_DOWNLOAD_QUEUE_SIZE # Use config directly
        except Exception as e:
            app_logger.error(f"Failed to get download queue size for {app_type}: {e}")
            download_queue_size = 0 # Assume 0 if error
            min_download_queue_size = -1 # Default to allow processing

        if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
            if check_restart(app_type, app_logger): continue

            # Get app-specific settings using settings_manager
            hunt_missing_count = keys_manager.settings_manager.get_setting(app_type, hunt_missing_setting, 0)
            hunt_upgrade_count = keys_manager.settings_manager.get_setting(app_type, hunt_upgrade_setting, 0)

            # Process Missing
            if process_missing and hunt_missing_count > 0:
                app_logger.info(f"Configured to look for {hunt_missing_count} missing items")
                try:
                    if process_missing(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info(f"No missing items processed for {app_type}")
                except Exception as e:
                    app_logger.error(f"Error processing missing items for {app_type}: {e}", exc_info=True)

                if check_restart(app_type, app_logger): continue
            elif hunt_missing_count <= 0:
                app_logger.info(f"Missing items search disabled ({hunt_missing_setting}=0)")

            # Process Upgrades
            if process_upgrades and hunt_upgrade_count > 0:
                app_logger.info(f"Configured to look for {hunt_upgrade_count} quality upgrades")
                try:
                    if process_upgrades(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info(f"No quality upgrades processed for {app_type}")
                except Exception as e:
                    app_logger.error(f"Error processing quality upgrades for {app_type}: {e}", exc_info=True)

                if check_restart(app_type, app_logger): continue
            elif hunt_upgrade_count <= 0:
                app_logger.info(f"Quality upgrades search disabled ({hunt_upgrade_setting}=0)")
        else:
            app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")

        calculate_reset_time(app_type)

        # Reload settings to get the current sleep duration for this app
        config.refresh_settings(app_type)
        # Use config directly for sleep duration
        current_sleep_duration = config.SLEEP_DURATION

        app_logger.info(f"{app_type} cycle complete. Sleeping {current_sleep_duration}s before next cycle...")

        # server_ip = get_ip_address() # Removed redundant logging of web interface URL
        # app_logger.info(f"Web interface available at http://{server_ip}:9705")

        sleep_start = time.time()
        sleep_end = sleep_start + current_sleep_duration

        while time.time() < sleep_end and not stop_threads:
            # Check for restart more frequently during sleep
            if check_restart(app_type, app_logger):
                 break # Break sleep loop to restart cycle

            remaining_sleep = sleep_end - time.time()
            check_interval = min(1, remaining_sleep) # Check every second or less

            # Log remaining time periodically (e.g., every 60 seconds)
            if int(time.time() - sleep_start) % 60 == 0 and remaining_sleep > 10:
                 remaining_min = int(remaining_sleep // 60)
                 app_logger.debug(f"{app_type} sleeping... {remaining_min}m remaining until next cycle")

            time.sleep(check_interval)

def start_app_threads():
    """Start threads for all configured apps"""
    # Check which apps are configured
    configured_apps = keys_manager.list_configured_apps()
    
    for app_type, is_configured in configured_apps.items():
        if is_configured and app_type not in app_threads:
            logger.info(f"Starting thread for {app_type}")
            thread = threading.Thread(target=app_specific_loop, args=(app_type,), daemon=True)
            app_threads[app_type] = thread
            thread.start()

def check_and_restart_threads():
    """Check if any threads have died and restart them"""
    for app_type, thread in list(app_threads.items()):
        if not thread.is_alive():
            logger.warning(f"{app_type} thread died, restarting...")
            del app_threads[app_type]
            new_thread = threading.Thread(target=app_specific_loop, args=(app_type,), daemon=True)
            app_threads[app_type] = new_thread
            new_thread.start()

def shutdown_threads():
    """Signal all threads to stop and wait for them to finish"""
    global stop_threads
    stop_threads = True
    logger.info("Shutting down all threads...")
    
    # Wait for all threads to finish
    for app_type, thread in app_threads.items():
        logger.info(f"Waiting for {app_type} thread to finish...")
        thread.join(timeout=10)
    
    logger.info("All threads stopped")

def start_huntarr():
    """Main entry point for Huntarr"""
    # Log configuration settings using the config module's function
    config.log_configuration(logger)

    try:
        # Start threads for all configured apps
        start_app_threads()

        # Main loop to monitor threads
        while not stop_threads: # Check stop_threads flag
            # Check if any configured apps need threads started
            start_app_threads()

            # Check if any threads have died and restart them
            check_and_restart_threads()

            # Sleep for a bit
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Huntarr stopped by user.")
        shutdown_threads()
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        shutdown_threads()
        sys.exit(1)