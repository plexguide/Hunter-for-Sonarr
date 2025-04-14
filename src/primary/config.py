#!/usr/bin/env python3
"""
Configuration module for Huntarr
Loads settings from the settings manager and provides them as constants
"""

import os
import sys
import logging
import importlib
import traceback
from src.primary import settings_manager
from src.primary.utils.logger import logger

# Get app type
APP_TYPE = settings_manager.get_app_type()

# API Configuration directly from settings_manager
API_URL = settings_manager.get_api_url()
API_KEY = settings_manager.get_api_key()

# Web UI is always enabled
ENABLE_WEB_UI = True

# Base settings - read directly from app section, no more nested huntarr section
API_TIMEOUT = settings_manager.get_setting(APP_TYPE, "api_timeout", 60)
DEBUG_MODE = settings_manager.get_setting(APP_TYPE, "debug_mode", False)
COMMAND_WAIT_DELAY = settings_manager.get_setting(APP_TYPE, "command_wait_delay", 1)
COMMAND_WAIT_ATTEMPTS = settings_manager.get_setting(APP_TYPE, "command_wait_attempts", 600)
MINIMUM_DOWNLOAD_QUEUE_SIZE = settings_manager.get_setting(APP_TYPE, "minimum_download_queue_size", -1)
MONITORED_ONLY = settings_manager.get_setting(APP_TYPE, "monitored_only", True)
LOG_REFRESH_INTERVAL_SECONDS = settings_manager.get_setting(APP_TYPE, "log_refresh_interval_seconds", 30)
SLEEP_DURATION = settings_manager.get_setting(APP_TYPE, "sleep_duration", 900)
STATE_RESET_INTERVAL_HOURS = settings_manager.get_setting(APP_TYPE, "state_reset_interval_hours", 168)
RANDOM_MISSING = settings_manager.get_setting(APP_TYPE, "random_missing", True)
RANDOM_UPGRADES = settings_manager.get_setting(APP_TYPE, "random_upgrades", True)

# App-specific settings - read directly from app section
if APP_TYPE == "sonarr":
    HUNT_MISSING_SHOWS = settings_manager.get_setting(APP_TYPE, "hunt_missing_shows", 1)
    HUNT_UPGRADE_EPISODES = settings_manager.get_setting(APP_TYPE, "hunt_upgrade_episodes", 0)
    SKIP_FUTURE_EPISODES = settings_manager.get_setting(APP_TYPE, "skip_future_episodes", True)
    SKIP_SERIES_REFRESH = settings_manager.get_setting(APP_TYPE, "skip_series_refresh", False)
    
elif APP_TYPE == "radarr":
    HUNT_MISSING_MOVIES = settings_manager.get_setting(APP_TYPE, "hunt_missing_movies", 1)
    HUNT_UPGRADE_MOVIES = settings_manager.get_setting(APP_TYPE, "hunt_upgrade_movies", 0)
    SKIP_FUTURE_RELEASES = settings_manager.get_setting(APP_TYPE, "skip_future_releases", True)
    SKIP_MOVIE_REFRESH = settings_manager.get_setting(APP_TYPE, "skip_movie_refresh", False)
    
elif APP_TYPE == "lidarr":
    HUNT_MISSING_ALBUMS = settings_manager.get_setting(APP_TYPE, "hunt_missing_albums", 1)
    HUNT_UPGRADE_TRACKS = settings_manager.get_setting(APP_TYPE, "hunt_upgrade_tracks", 0)
    SKIP_FUTURE_RELEASES = settings_manager.get_setting(APP_TYPE, "skip_future_releases", True)
    SKIP_ARTIST_REFRESH = settings_manager.get_setting(APP_TYPE, "skip_artist_refresh", False)
    
elif APP_TYPE == "readarr":
    HUNT_MISSING_BOOKS = settings_manager.get_setting(APP_TYPE, "hunt_missing_books", 1)
    HUNT_UPGRADE_BOOKS = settings_manager.get_setting(APP_TYPE, "hunt_upgrade_books", 0)
    SKIP_FUTURE_RELEASES = settings_manager.get_setting(APP_TYPE, "skip_future_releases", True)
    SKIP_AUTHOR_REFRESH = settings_manager.get_setting(APP_TYPE, "skip_author_refresh", False)

# For backward compatibility with Sonarr (the initial implementation)
if APP_TYPE != "sonarr":
    # Add Sonarr specific variables for backward compatibility
    HUNT_MISSING_SHOWS = 0
    HUNT_UPGRADE_EPISODES = 0
    SKIP_FUTURE_EPISODES = True
    SKIP_SERIES_REFRESH = False

# For backward compatibility with Radarr
if APP_TYPE not in ["sonarr", "radarr"]:
    # Add Radarr specific variables for backward compatibility
    HUNT_MISSING_MOVIES = 0
    HUNT_UPGRADE_MOVIES = 0
    SKIP_MOVIE_REFRESH = False

# For backward compatibility with Lidarr
if APP_TYPE not in ["sonarr", "radarr", "lidarr"]:
    # Add Lidarr specific variables for backward compatibility
    HUNT_MISSING_ALBUMS = 0
    HUNT_UPGRADE_TRACKS = 0
    SKIP_ARTIST_REFRESH = False

# For backward compatibility with Readarr
if APP_TYPE not in ["sonarr", "radarr", "lidarr", "readarr"]:
    # Add Readarr specific variables for backward compatibility
    HUNT_MISSING_BOOKS = 0
    HUNT_UPGRADE_BOOKS = 0
    SKIP_AUTHOR_REFRESH = False

# Determine the hunt mode based on settings
def determine_hunt_mode():
    """Determine the hunt mode based on current settings"""
    if APP_TYPE == "sonarr":
        if HUNT_MISSING_SHOWS > 0 and HUNT_UPGRADE_EPISODES > 0:
            return "both"
        elif HUNT_MISSING_SHOWS > 0:
            return "missing"
        elif HUNT_UPGRADE_EPISODES > 0:
            return "upgrade"
        else:
            return "disabled"
    elif APP_TYPE == "radarr":
        if HUNT_MISSING_MOVIES > 0 and HUNT_UPGRADE_MOVIES > 0:
            return "both"
        elif HUNT_MISSING_MOVIES > 0:
            return "missing"
        elif HUNT_UPGRADE_MOVIES > 0:
            return "upgrade"
        else:
            return "disabled"
    elif APP_TYPE == "lidarr":
        if HUNT_MISSING_ALBUMS > 0 and HUNT_UPGRADE_TRACKS > 0:
            return "both"
        elif HUNT_MISSING_ALBUMS > 0:
            return "missing"
        elif HUNT_UPGRADE_TRACKS > 0:
            return "upgrade"
        else:
            return "disabled"
    elif APP_TYPE == "readarr":
        if HUNT_MISSING_BOOKS > 0 and HUNT_UPGRADE_BOOKS > 0:
            return "both"
        elif HUNT_MISSING_BOOKS > 0:
            return "missing"
        elif HUNT_UPGRADE_BOOKS > 0:
            return "upgrade"
        else:
            return "disabled"
    else:
        return "disabled"

# Configure logging
def configure_logging(app_logger=None):
    """Configure logging based on DEBUG_MODE setting"""
    try:
        # Configure based on DEBUG_MODE if a logger is provided
        if app_logger:
            if DEBUG_MODE:
                app_logger.setLevel(logging.DEBUG)
            else:
                app_logger.setLevel(logging.INFO)
        
        # Always configure the root logger
        root_logger = logging.getLogger()
        if DEBUG_MODE:
            root_logger.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.INFO)
        
        return app_logger or root_logger
    except Exception as e:
        # Print directly to stderr since logging might not be working
        print(f"CRITICAL ERROR in configure_logging: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        # Try to log it anyway
        if logger:
            logger.error(f"Error in configure_logging: {str(e)}")
            logger.error(traceback.format_exc())
        raise

# Log the configuration
def log_configuration(app_logger=None):
    """Log the current configuration settings"""
    log = app_logger or logger
    
    log.info(f"Configuration loaded for app type: {APP_TYPE}")
    log.info(f"API URL: {API_URL}")
    log.info(f"API Key: {'[REDACTED]' if API_KEY else 'Not Set'}")
    log.info(f"Debug Mode: {DEBUG_MODE}")
    log.info(f"Hunt Mode: {determine_hunt_mode()}")
    log.info(f"Sleep Duration: {SLEEP_DURATION} seconds")
    log.info(f"State Reset Interval: {STATE_RESET_INTERVAL_HOURS} hours")
    log.info(f"Monitored Only: {MONITORED_ONLY}")
    log.info(f"Minimum Download Queue Size: {MINIMUM_DOWNLOAD_QUEUE_SIZE}")
    
    # App-specific settings
    if APP_TYPE == "sonarr":
        log.info(f"Hunt Missing Shows: {HUNT_MISSING_SHOWS}")
        log.info(f"Hunt Upgrade Episodes: {HUNT_UPGRADE_EPISODES}")
        log.info(f"Skip Future Episodes: {SKIP_FUTURE_EPISODES}")
        log.info(f"Skip Series Refresh: {SKIP_SERIES_REFRESH}")
    elif APP_TYPE == "radarr":
        log.info(f"Hunt Missing Movies: {HUNT_MISSING_MOVIES}")
        log.info(f"Hunt Upgrade Movies: {HUNT_UPGRADE_MOVIES}")
        log.info(f"Skip Future Releases: {SKIP_FUTURE_RELEASES}")
        log.info(f"Skip Movie Refresh: {SKIP_MOVIE_REFRESH}")
    elif APP_TYPE == "lidarr":
        log.info(f"Hunt Missing Albums: {HUNT_MISSING_ALBUMS}")
        log.info(f"Hunt Upgrade Tracks: {HUNT_UPGRADE_TRACKS}")
        log.info(f"Skip Future Releases: {SKIP_FUTURE_RELEASES}")
        log.info(f"Skip Artist Refresh: {SKIP_ARTIST_REFRESH}")
    elif APP_TYPE == "readarr":
        log.info(f"Hunt Missing Books: {HUNT_MISSING_BOOKS}")
        log.info(f"Hunt Upgrade Books: {HUNT_UPGRADE_BOOKS}")
        log.info(f"Skip Future Releases: {SKIP_FUTURE_RELEASES}")
        log.info(f"Skip Author Refresh: {SKIP_AUTHOR_REFRESH}")

# Refresh settings from file
def refresh_settings(app_type=None):
    """
    Refresh global settings from config file.
    
    Args:
        app_type: Optional app type to refresh settings for. If None, uses the global APP_TYPE.
    """
    # Import at function level to avoid circular import
    from src.primary.settings_manager import load_settings, get_setting
    
    # If app_type is provided, temporarily override the global APP_TYPE
    global APP_TYPE
    original_app_type = APP_TYPE
    
    try:
        if app_type is not None:
            APP_TYPE = app_type
            
        # Reload all settings for the current APP_TYPE
        global MONITORED_ONLY, LOG_REFRESH_INTERVAL_SECONDS, SLEEP_DURATION
        global STATE_RESET_INTERVAL_HOURS, RANDOM_MISSING, RANDOM_UPGRADES
        global API_TIMEOUT, COMMAND_WAIT_DELAY, COMMAND_WAIT_ATTEMPTS, MINIMUM_DOWNLOAD_QUEUE_SIZE
        
        # Reload all the settings
        MONITORED_ONLY = get_setting(APP_TYPE, "monitored_only", True)
        LOG_REFRESH_INTERVAL_SECONDS = get_setting(APP_TYPE, "log_refresh_interval_seconds", 30)
        SLEEP_DURATION = get_setting(APP_TYPE, "sleep_duration", 900)
        STATE_RESET_INTERVAL_HOURS = get_setting(APP_TYPE, "state_reset_interval_hours", 168)
        RANDOM_MISSING = get_setting(APP_TYPE, "random_missing", True)
        RANDOM_UPGRADES = get_setting(APP_TYPE, "random_upgrades", True)
        
        # App-specific settings
        # Load app-specific settings based on current APP_TYPE
        if APP_TYPE == "sonarr":
            global HUNT_MISSING_SHOWS, HUNT_UPGRADE_EPISODES
            global SKIP_FUTURE_EPISODES, SKIP_SERIES_REFRESH
            HUNT_MISSING_SHOWS = get_setting(APP_TYPE, "hunt_missing_shows", 1)
            HUNT_UPGRADE_EPISODES = get_setting(APP_TYPE, "hunt_upgrade_episodes", 0)
            SKIP_FUTURE_EPISODES = get_setting(APP_TYPE, "skip_future_episodes", True)
            SKIP_SERIES_REFRESH = get_setting(APP_TYPE, "skip_series_refresh", False)
        elif APP_TYPE == "radarr":
            global HUNT_MISSING_MOVIES, HUNT_UPGRADE_MOVIES
            global SKIP_FUTURE_RELEASES, SKIP_MOVIE_REFRESH
            HUNT_MISSING_MOVIES = get_setting(APP_TYPE, "hunt_missing_movies", 1)
            HUNT_UPGRADE_MOVIES = get_setting(APP_TYPE, "hunt_upgrade_movies", 0)
            SKIP_FUTURE_RELEASES = get_setting(APP_TYPE, "skip_future_releases", True)
            SKIP_MOVIE_REFRESH = get_setting(APP_TYPE, "skip_movie_refresh", False)
        # Add other app types as needed
        
        # Log the new configuration
        log_configuration()
    finally:
        # Restore original APP_TYPE if it was changed
        if app_type is not None:
            APP_TYPE = original_app_type

# Configure logging based on settings
configure_logging(logger)