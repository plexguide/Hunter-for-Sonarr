#!/usr/bin/env python3
"""
Configuration module for Huntarr
Provides utility functions to access settings via settings_manager
and perform configuration-related tasks like logging.
Removes the old concept of loading a single app's config into global constants.
"""

import os
import sys
import logging
import traceback
from src.primary import settings_manager
from src.primary.utils.logger import logger, get_logger # Import get_logger

# Removed global constants like APP_TYPE, API_URL, API_KEY, SLEEP_DURATION etc.
# Settings should be fetched directly using settings_manager when needed.

# Determine the hunt mode for a specific app
def determine_hunt_mode(app_name: str) -> str:
    """Determine the hunt mode for a specific app based on its settings."""
    # Fetch settings directly for the given app
    hunt_missing = 0
    hunt_upgrade = 0

    if app_name == "sonarr":
        hunt_missing = settings_manager.get_setting(app_name, "hunt_missing_shows", 0)
        hunt_upgrade = settings_manager.get_setting(app_name, "hunt_upgrade_episodes", 0)
    elif app_name == "radarr":
        hunt_missing = settings_manager.get_setting(app_name, "hunt_missing_movies", 0)
        hunt_upgrade = settings_manager.get_setting(app_name, "hunt_upgrade_movies", 0)
    elif app_name.lower() == 'lidarr':
        # Use hunt_missing_items instead of hunt_missing_albums
        hunt_missing = settings_manager.get_setting(app_name, "hunt_missing_items", 0)
        # Use hunt_upgrade_items instead of hunt_upgrade_albums
        hunt_upgrade = settings_manager.get_setting(app_name, "hunt_upgrade_items", 0) 
        
        # For Lidarr, also include the hunt_missing_mode
        hunt_missing_mode = settings_manager.get_setting(app_name, "hunt_missing_mode", "artist")
    elif app_name == "readarr":
        hunt_missing = settings_manager.get_setting(app_name, "hunt_missing_books", 0)
        hunt_upgrade = settings_manager.get_setting(app_name, "hunt_upgrade_books", 0)
    else:
        # Handle unknown app types if necessary, or just return disabled
        return "disabled"

    # Determine mode based on fetched values
    if hunt_missing > 0 and hunt_upgrade > 0:
        return "both"
    elif hunt_missing > 0:
        return "missing"
    elif hunt_upgrade > 0:
        return "upgrade"
    else:
        return "disabled"

# Configure logging level based on an app's debug setting
def configure_logging(app_name: str = None):
    """Configure logging level based on the debug setting of a specific app or globally."""
    try:
        debug_mode = False
        log_instance = logger # Default to the main logger

        if app_name:
            debug_mode = settings_manager.get_setting(app_name, "debug_mode", False)
            log_instance = get_logger(app_name) # Get the specific app logger
        # else: # Optional: Could check a global debug setting if needed
            # debug_mode = settings_manager.get_setting("global", "debug_mode", False)

        level = logging.DEBUG if debug_mode else logging.INFO

        # Configure the specific app logger
        if app_name and log_instance:
            log_instance.setLevel(level)

        # Always configure the root logger as well (or adjust based on desired behavior)
        # If you want root logger level controlled by a specific app, this needs refinement.
        # For now, let's set the root logger based on the *last* app configured or global.
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Optional: Configure handlers if not done elsewhere
        # Example: Ensure handlers exist and set their level
        # for handler in log_instance.handlers:
        #     handler.setLevel(level)
        # for handler in root_logger.handlers:
        #     handler.setLevel(level)

    except Exception as e:
        print(f"CRITICAL ERROR in configure_logging for app '{app_name}': {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        # Try to log it anyway
        if logger:
            logger.error(f"Error in configure_logging for app '{app_name}': {str(e)}")
            logger.error(traceback.format_exc())
        # Decide whether to raise or continue
        # raise

# Log the configuration for a specific app
def log_configuration(app_name: str):
    """Log the current configuration settings for a specific app."""
    log = get_logger(app_name) # Use the specific app's logger
    settings = settings_manager.load_settings(app_name) # Corrected function name

    if not settings:
        log.error(f"Could not load settings for app: {app_name}. Cannot log configuration.")
        return

    api_url = settings.get("api_url", "")
    api_key = settings.get("api_key", "")
    debug_mode = settings.get("debug_mode", False)
    sleep_duration = settings.get("sleep_duration", 900)
    state_reset_interval = settings.get("state_reset_interval_hours", 168)
    monitored_only = settings.get("monitored_only", True)
    min_queue_size = settings.get("minimum_download_queue_size", -1)

    log.info(f"--- Configuration for {app_name} ---")
    log.info(f"API URL: {api_url}")
    log.info(f"API Key: {'[REDACTED]' if api_key else 'Not Set'}")
    log.info(f"Debug Mode: {debug_mode}")
    log.info(f"Hunt Mode: {determine_hunt_mode(app_name)}")
    log.info(f"Sleep Duration: {sleep_duration} seconds")
    log.info(f"State Reset Interval: {state_reset_interval} hours")
    log.info(f"Monitored Only: {monitored_only}")
    log.info(f"Minimum Download Queue Size: {min_queue_size}")

    # App-specific settings logging
    if app_name == "sonarr":
        log.info(f"Hunt Missing Shows: {settings.get('hunt_missing_shows', 0)}")
        log.info(f"Hunt Upgrade Episodes: {settings.get('hunt_upgrade_episodes', 0)}")
        log.info(f"Skip Future Episodes: {settings.get('skip_future_episodes', True)}")
        log.info(f"Skip Series Refresh: {settings.get('skip_series_refresh', False)}")
    elif app_name == "radarr":
        log.info(f"Hunt Missing Movies: {settings.get('hunt_missing_movies', 0)}")
        log.info(f"Hunt Upgrade Movies: {settings.get('hunt_upgrade_movies', 0)}")
        log.info(f"Skip Future Releases: {settings.get('skip_future_releases', True)}")
        log.info(f"Skip Movie Refresh: {settings.get('skip_movie_refresh', False)}")
    elif app_name.lower() == 'lidarr':
        log.info(f"Mode: {settings.get('hunt_missing_mode', 'artist')}")
        log.info(f"Hunt Missing Items: {settings.get('hunt_missing_items', 0)}")
        # Use hunt_upgrade_items
        log.info(f"Hunt Upgrade Items: {settings.get('hunt_upgrade_items', 0)}") 
        log.info(f"Sleep Duration: {settings.get('sleep_duration', 900)} seconds")
        log.info(f"State Reset Interval: {settings.get('state_reset_interval_hours', 168)} hours")
        log.info(f"Monitored Only: {settings.get('monitored_only', True)}")
        log.info(f"Minimum Download Queue Size: {settings.get('minimum_download_queue_size', -1)}")
    elif app_name == "readarr":
        log.info(f"Hunt Missing Books: {settings.get('hunt_missing_books', 0)}")
        log.info(f"Hunt Upgrade Books: {settings.get('hunt_upgrade_books', 0)}")
        log.info(f"Skip Future Releases: {settings.get('skip_future_releases', True)}")
        log.info(f"Skip Author Refresh: {settings.get('skip_author_refresh', False)}")
    log.info(f"--- End Configuration for {app_name} ---")

# Removed refresh_settings function - settings are loaded dynamically by settings_manager

# Initial logging configuration (optional, could be done in main startup)
# configure_logging() # Configure root logger based on global/default debug setting if desired