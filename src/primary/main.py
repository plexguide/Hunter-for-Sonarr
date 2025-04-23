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
from src.primary.config import SLEEP_DURATION, MINIMUM_DOWNLOAD_QUEUE_SIZE, log_configuration, refresh_settings
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
        importlib.reload(sys.modules['src.primary.config'])
        logger.debug("Reloaded src.primary.config module")
    except (KeyError, ImportError) as e:
        logger.error(f"Error reloading modules: {e}")

# Find the refresh_settings function and modify it to accept an app_type parameter
def refresh_settings(app_type=None):
    """
    Refresh settings from the config file.
    
    Args:
        app_type: Optional app type to refresh settings for. If None, uses the global APP_TYPE.
    """
    from src.primary.config import log_configuration
    
    # If app_type is not provided, use the global APP_TYPE
    if app_type is None:
        from src.primary.config import APP_TYPE as current_app_type
        app_type = current_app_type
        
    # Log the refresh
    logger.debug(f"Refreshing settings for {app_type}")
    
    # Call the original log_configuration function
    log_configuration()

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
    
    server_ip = get_ip_address()
    app_logger.info(f"Web interface available at http://{server_ip}:9705")
    
    # Import necessary modules based on app type
    if app_type == "sonarr":
        from src.primary.apps.sonarr.missing import process_missing_episodes
        from src.primary.apps.sonarr.upgrade import process_cutoff_upgrades
        from src.primary.api import get_download_queue_size as sonarr_get_download_queue_size
    elif app_type == "radarr":
        from src.primary.apps.radarr.missing import process_missing_movies
        from src.primary.apps.radarr.upgrade import process_cutoff_upgrades
        from src.primary.apps.radarr.api import get_download_queue_size
    elif app_type == "lidarr":
        from src.primary.apps.lidarr.missing import process_missing_albums
        from src.primary.apps.lidarr.upgrade import process_cutoff_upgrades
        from src.primary.apps.lidarr.api import get_download_queue_size
    elif app_type == "readarr":
        from src.primary.apps.readarr.missing import process_missing_books
        from src.primary.apps.readarr.upgrade import process_cutoff_upgrades
        # Placeholder for Readarr-specific API functions
        sonarr_get_download_queue_size = lambda: 0  # Placeholder
    
    # Get API keys for this app
    api_url, api_key = keys_manager.get_api_keys(app_type)
    
    # Set the API credentials for this thread context
    os.environ[f"{app_type.upper()}_API_URL"] = api_url
    os.environ[f"{app_type.upper()}_API_KEY"] = api_key
    
    while not stop_threads:
        restart_cycles[app_type] = False
        
        # Always reload settings from huntarr.json at the start of each cycle
        refresh_settings(app_type)
        
        check_state_reset(app_type)
        
        app_logger.info(f"=== Starting Huntarr {app_type} cycle ===")
        
        # Import check_connection with the correct app type
        import_module = __import__('src.primary.api', fromlist=[''])
        check_connection = getattr(import_module, 'check_connection')
        
        # Override the global APP_TYPE for this thread
        os.environ["APP_TYPE"] = app_type
        
        api_connected = False
        
        connection_attempts = 0
        while not api_connected and not restart_cycles[app_type] and not stop_threads:
            refresh_settings(app_type)  # Ensure latest settings are loaded
            
            api_connected = check_connection(app_type)
            if not api_connected:
                app_logger.error(f"Cannot connect to {app_type.title()}. Please check your API URL and API key.")
                app_logger.info(f"Will retry in 10 seconds...")
                
                for _ in range(10):
                    time.sleep(1)
                    if restart_cycles[app_type] or stop_threads:
                        break
                
                connection_attempts += 1
                if connection_attempts >= 3:
                    app_logger.warning(f"Multiple failed connection attempts to {app_type.title()}. Will try again next cycle.")
                    break
            
            if restart_cycles[app_type]:
                app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                continue
        
        if not api_connected:
            app_logger.error(f"Connection to {app_type} failed, skipping this cycle.")
            time.sleep(10)
            continue
        
        processing_done = False
        
        # App-specific processing logic
        if app_type == "sonarr":
            # Get download queue size with the app-specific function
            download_queue_size = sonarr_get_download_queue_size()
            min_download_queue_size = MINIMUM_DOWNLOAD_QUEUE_SIZE
            
            if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
                if restart_cycles[app_type]:
                    app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                    continue
                
                # Get app-specific settings
                from src.primary.config import HUNT_MISSING_SHOWS, HUNT_UPGRADE_EPISODES
                
                if HUNT_MISSING_SHOWS > 0:
                    app_logger.info(f"Configured to look for {HUNT_MISSING_SHOWS} missing shows")
                    if process_missing_episodes(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No missing episodes processed - check if you have any missing episodes in Sonarr")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Missing shows search disabled (HUNT_MISSING_SHOWS=0)")
                
                if HUNT_UPGRADE_EPISODES > 0:
                    app_logger.info(f"Configured to look for {HUNT_UPGRADE_EPISODES} quality upgrades")
                    if process_cutoff_upgrades(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No quality upgrades processed - check if you have any cutoff unmet episodes in Sonarr")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Quality upgrades search disabled (HUNT_UPGRADE_EPISODES=0)")
            else:
                app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")
        
        elif app_type == "radarr":
            # Get download queue size with the app-specific function
            download_queue_size = get_download_queue_size()
            min_download_queue_size = MINIMUM_DOWNLOAD_QUEUE_SIZE
            
            if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
                if restart_cycles[app_type]:
                    app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                    continue
                
                # Get app-specific settings
                from src.primary.config import HUNT_MISSING_MOVIES, HUNT_UPGRADE_MOVIES
                
                if HUNT_MISSING_MOVIES > 0:
                    app_logger.info(f"Configured to look for {HUNT_MISSING_MOVIES} missing movies")
                    if process_missing_movies(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No missing movies processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Missing movies search disabled (HUNT_MISSING_MOVIES=0)")
                
                if HUNT_UPGRADE_MOVIES > 0:
                    app_logger.info(f"Configured to look for {HUNT_UPGRADE_MOVIES} quality upgrades")
                    if process_cutoff_upgrades(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No quality upgrades processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Quality upgrades search disabled (HUNT_UPGRADE_MOVIES=0)")
            else:
                app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")
        
        elif app_type == "lidarr":
            # Get download queue size with the app-specific function
            download_queue_size = get_download_queue_size()
            min_download_queue_size = MINIMUM_DOWNLOAD_QUEUE_SIZE
            
            if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
                if restart_cycles[app_type]:
                    app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                    continue
                
                # Get app-specific settings
                from src.primary.config import HUNT_MISSING_ALBUMS, HUNT_UPGRADE_TRACKS
                
                if HUNT_MISSING_ALBUMS > 0:
                    app_logger.info(f"Configured to look for {HUNT_MISSING_ALBUMS} missing albums")
                    if process_missing_albums(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No missing albums processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Missing albums search disabled (HUNT_MISSING_ALBUMS=0)")
                
                if HUNT_UPGRADE_TRACKS > 0:
                    app_logger.info(f"Configured to look for {HUNT_UPGRADE_TRACKS} quality upgrades")
                    if process_cutoff_upgrades(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No quality upgrades processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Quality upgrades search disabled (HUNT_UPGRADE_TRACKS=0)")
            else:
                app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")
        
        elif app_type == "readarr":
            # Get download queue size with the app-specific function
            download_queue_size = sonarr_get_download_queue_size()  # Placeholder - will be replaced with readarr-specific function
            min_download_queue_size = MINIMUM_DOWNLOAD_QUEUE_SIZE
            
            if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
                if restart_cycles[app_type]:
                    app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                    continue
                
                # Get app-specific settings
                from src.primary.config import HUNT_MISSING_BOOKS, HUNT_UPGRADE_BOOKS
                
                if HUNT_MISSING_BOOKS > 0:
                    app_logger.info(f"Configured to look for {HUNT_MISSING_BOOKS} missing books")
                    if process_missing_books(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No missing books processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Missing books search disabled (HUNT_MISSING_BOOKS=0)")
                
                if HUNT_UPGRADE_BOOKS > 0:
                    app_logger.info(f"Configured to look for {HUNT_UPGRADE_BOOKS} quality upgrades")
                    if process_cutoff_upgrades(lambda: restart_cycles[app_type]):
                        processing_done = True
                    else:
                        app_logger.info("No quality upgrades processed - feature not yet fully implemented")
                    
                    if restart_cycles[app_type]:
                        app_logger.warning(f"⚠️ Restarting {app_type} cycle due to settings change... ⚠️")
                        continue
                else:
                    app_logger.info("Quality upgrades search disabled (HUNT_UPGRADE_BOOKS=0)")
            else:
                app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")
        
        calculate_reset_time(app_type)
        
        refresh_settings(app_type)
        from src.primary.config import SLEEP_DURATION as CURRENT_SLEEP_DURATION
        
        app_logger.info(f"{app_type} cycle complete. Sleeping {CURRENT_SLEEP_DURATION}s before next cycle...")
        
        server_ip = get_ip_address()
        app_logger.info(f"Web interface available at http://{server_ip}:9705")
        
        sleep_start = time.time()
        sleep_end = sleep_start + CURRENT_SLEEP_DURATION
        
        while time.time() < sleep_end and not restart_cycles[app_type] and not stop_threads:
            time.sleep(min(1, sleep_end - time.time()))
            
            if int((time.time() - sleep_start) % 60) == 0 and time.time() < sleep_end - 10:
                remaining = int(sleep_end - time.time())
                app_logger.debug(f"{app_type} sleeping... {remaining}s remaining until next cycle")
            
            if restart_cycles[app_type]:
                app_logger.warning(f"⚠️ {app_type} sleep interrupted due to settings change. Restarting cycle immediately... ⚠️")
                break

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

def log_configuration(log):
    """Log the current configuration settings"""
    # Change the startup message to just say "Huntarr" instead of "Huntarr [Sonarr Edition]"
    log.info("=" * 60)
    log.info(f"Starting Huntarr v{__version__}")
    log.info("=" * 60)
    
    # ...existing code...

def start_huntarr():
    """Main entry point for Huntarr"""
    # Log configuration settings
    log_configuration(logger)
    
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