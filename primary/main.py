#!/usr/bin/env python3
"""
Huntarr - Main entry point for the application
Simplified to support only Sonarr
"""

import time
import sys
import os
import socket
import signal
import importlib
import logging

# Define the version number
__version__ = "1.0.0"

# Set up logging first to avoid circular imports
from primary.utils.logger import setup_logger
logger = setup_logger()

# Now import the rest of the modules
from primary.config import SLEEP_DURATION, MINIMUM_DOWNLOAD_QUEUE_SIZE, log_configuration, refresh_settings
from primary.state import check_state_reset, calculate_reset_time
from primary.utils.app_utils import get_ip_address
from primary import keys_manager

# Flag to indicate if cycle should restart
restart_cycle = False
stop_process = False

def signal_handler(signum, frame):
    """Handle signals from the web UI for cycle restart"""
    if signum == signal.SIGUSR1:
        global restart_cycle
        logger.info("🔄 Received restart signal for Sonarr")
        restart_cycle = True

# Register signal handler for SIGUSR1
signal.signal(signal.SIGUSR1, signal_handler)

def force_reload_all_modules():
    """Force reload of all relevant modules to ensure fresh settings"""
    try:
        importlib.reload(sys.modules['primary.config'])
        logger.debug("Reloaded primary.config module")
    except (KeyError, ImportError) as e:
        logger.error(f"Error reloading modules: {e}")

def main_loop():
    """
    Main processing loop for Sonarr
    """
    global restart_cycle
    
    # Get app-specific logger
    from primary.utils.logger import get_logger
    app_logger = get_logger("sonarr")
    
    app_logger.info("=== Huntarr starting for Sonarr ===")
    
    server_ip = get_ip_address()
    app_logger.info(f"Web interface available at http://{server_ip}:9705")
    
    # Import necessary modules
    from primary.apps.sonarr.missing import process_missing_episodes
    from primary.apps.sonarr.upgrade import process_cutoff_upgrades
    from primary.api import get_download_queue_size as sonarr_get_download_queue_size
    
    # Get API keys
    api_url, api_key = keys_manager.get_api_keys("sonarr")
    
    # Set the API credentials
    os.environ["SONARR_API_URL"] = api_url
    os.environ["SONARR_API_KEY"] = api_key
    
    while not stop_process:
        restart_cycle = False
        
        # Always reload settings from huntarr.json at the start of each cycle
        refresh_settings("sonarr")
        
        check_state_reset("sonarr")
        
        app_logger.info("=== Starting Huntarr Sonarr cycle ===")
        
        # Import check_connection
        import_module = __import__('primary.api', fromlist=[''])
        check_connection = getattr(import_module, 'check_connection')
        
        # Override the global APP_TYPE for this process
        os.environ["APP_TYPE"] = "sonarr"
        
        api_connected = False
        
        connection_attempts = 0
        while not api_connected and not restart_cycle and not stop_process:
            refresh_settings("sonarr")  # Ensure latest settings are loaded
            
            api_connected = check_connection("sonarr")
            if not api_connected:
                app_logger.error("Cannot connect to Sonarr. Please check your API URL and API key.")
                app_logger.info("Will retry in 10 seconds...")
                
                for _ in range(10):
                    time.sleep(1)
                    if restart_cycle or stop_process:
                        break
                
                connection_attempts += 1
                if connection_attempts >= 3:
                    app_logger.warning("Multiple failed connection attempts to Sonarr. Will try again next cycle.")
                    break
            
            if restart_cycle:
                app_logger.warning("⚠️ Restarting Sonarr cycle due to settings change... ⚠️")
                continue
        
        if not api_connected:
            app_logger.error("Connection to Sonarr failed, skipping this cycle.")
            time.sleep(10)
            continue
        
        processing_done = False
        
        # Get download queue size with the app-specific function
        download_queue_size = sonarr_get_download_queue_size()
        min_download_queue_size = MINIMUM_DOWNLOAD_QUEUE_SIZE
        
        if min_download_queue_size < 0 or (min_download_queue_size >= 0 and download_queue_size <= min_download_queue_size):
            if restart_cycle:
                app_logger.warning("⚠️ Restarting Sonarr cycle due to settings change... ⚠️")
                continue
            
            # Get app-specific settings
            from primary.config import HUNT_MISSING_SHOWS, HUNT_UPGRADE_EPISODES
            
            if HUNT_MISSING_SHOWS > 0:
                app_logger.info(f"Configured to look for {HUNT_MISSING_SHOWS} missing shows")
                if process_missing_episodes(lambda: restart_cycle):
                    processing_done = True
                else:
                    app_logger.info("No missing episodes processed - check if you have any missing episodes in Sonarr")
                
                if restart_cycle:
                    app_logger.warning("⚠️ Restarting Sonarr cycle due to settings change... ⚠️")
                    continue
            else:
                app_logger.info("Missing shows search disabled (HUNT_MISSING_SHOWS=0)")
            
            if HUNT_UPGRADE_EPISODES > 0:
                app_logger.info(f"Configured to look for {HUNT_UPGRADE_EPISODES} quality upgrades")
                if process_cutoff_upgrades(lambda: restart_cycle):
                    processing_done = True
                else:
                    app_logger.info("No quality upgrades processed - check if you have any cutoff unmet episodes in Sonarr")
                
                if restart_cycle:
                    app_logger.warning("⚠️ Restarting Sonarr cycle due to settings change... ⚠️")
                    continue
            else:
                app_logger.info("Quality upgrades search disabled (HUNT_UPGRADE_EPISODES=0)")
        else:
            app_logger.info(f"Download queue size ({download_queue_size}) is above the minimum threshold ({min_download_queue_size}). Skipped processing.")
        
        calculate_reset_time("sonarr")
        
        refresh_settings("sonarr")
        from primary.config import SLEEP_DURATION as CURRENT_SLEEP_DURATION
        
        app_logger.info(f"Sonarr cycle complete. Sleeping {CURRENT_SLEEP_DURATION}s before next cycle...")
        
        server_ip = get_ip_address()
        app_logger.info(f"Web interface available at http://{server_ip}:9705")
        
        sleep_start = time.time()
        sleep_end = sleep_start + CURRENT_SLEEP_DURATION
        
        while time.time() < sleep_end and not restart_cycle and not stop_process:
            time.sleep(min(1, sleep_end - time.time()))
            
            if int((time.time() - sleep_start) % 60) == 0 and time.time() < sleep_end - 10:
                remaining = int(sleep_end - time.time())
                app_logger.debug(f"Sonarr sleeping... {remaining}s remaining until next cycle")
            
            if restart_cycle:
                app_logger.warning("⚠️ Sonarr sleep interrupted due to settings change. Restarting cycle immediately... ⚠️")
                break

def log_configuration(log):
    """Log the current configuration settings"""
    # Change the startup message to just say "Huntarr Sonarr"
    log.info("=" * 60)
    log.info(f"Starting Huntarr Sonarr v{__version__}")
    log.info("=" * 60)

def main():
    """Main entry point for Huntarr"""
    # Log configuration settings
    log_configuration(logger)
    
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Huntarr stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()