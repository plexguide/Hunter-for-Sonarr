#!/usr/bin/env python3
"""
Configuration module for Huntarr
Loads settings from the settings manager and provides them as constants
Simplified for Sonarr only
"""

import os
import sys
import logging
import importlib
from primary import settings_manager
from primary.utils.logger import logger

# App type is always sonarr
APP_TYPE = "sonarr"

# API Configuration directly from settings_manager
API_URL, API_KEY = settings_manager.get_api_keys()

# Web UI is always enabled
ENABLE_WEB_UI = True

# Base settings - read directly from app section
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

# Sonarr-specific settings
HUNT_MISSING_SHOWS = settings_manager.get_setting(APP_TYPE, "hunt_missing_shows", 1)
HUNT_UPGRADE_EPISODES = settings_manager.get_setting(APP_TYPE, "hunt_upgrade_episodes", 0)
SKIP_FUTURE_EPISODES = settings_manager.get_setting(APP_TYPE, "skip_future_episodes", True)
SKIP_SERIES_REFRESH = settings_manager.get_setting(APP_TYPE, "skip_series_refresh", False)

# Determine the hunt mode based on settings
def determine_hunt_mode():
    """Determine the hunt mode based on current settings"""
    if HUNT_MISSING_SHOWS > 0 and HUNT_UPGRADE_EPISODES > 0:
        return "both"
    elif HUNT_MISSING_SHOWS > 0:
        return "missing"
    elif HUNT_UPGRADE_EPISODES > 0:
        return "upgrade"
    else:
        return "none"

# Configure logging
def configure_logging(app_logger=None):
    """Configure logging based on DEBUG_MODE setting"""
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

# Log the configuration
def log_configuration(app_logger=None):
    """Log the current configuration settings"""
    log = app_logger or logger
    
    log.info(f"API URL: {API_URL}")
    log.info(f"API Key: {'[REDACTED]' if API_KEY else 'Not Set'}")
    log.info(f"Debug Mode: {DEBUG_MODE}")
    log.info(f"Hunt Mode: {determine_hunt_mode()}")
    log.info(f"Sleep Duration: {SLEEP_DURATION} seconds")
    log.info(f"State Reset Interval: {STATE_RESET_INTERVAL_HOURS} hours")
    log.info(f"Monitored Only: {MONITORED_ONLY}")
    log.info(f"Minimum Download Queue Size: {MINIMUM_DOWNLOAD_QUEUE_SIZE}")
    log.info(f"Hunt Missing Shows: {HUNT_MISSING_SHOWS}")
    log.info(f"Hunt Upgrade Episodes: {HUNT_UPGRADE_EPISODES}")
    log.info(f"Skip Future Episodes: {SKIP_FUTURE_EPISODES}")
    log.info(f"Skip Series Refresh: {SKIP_SERIES_REFRESH}")

# Refresh settings from file
def refresh_settings(app_type=None):
    """Refresh settings from file and update module globals"""
    # Reimport this module to refresh settings
    try:
        importlib.reload(sys.modules[__name__])
        return True
    except Exception as e:
        logger.error(f"Error refreshing settings: {e}")
        return False

# Configure logging based on settings
configure_logging(logger)