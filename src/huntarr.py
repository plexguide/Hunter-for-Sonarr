#!/usr/bin/env python3
import os
from src.utils.logger import logger
'''TODO add a function here that starts the FLask / api app'''
"""
Huntarr-Sonarr - Automatically search for missing episodes and episode upgrades
"""


settings = {}
# Environment variables with defaults
settings['API_KEY'] = os.environ.get('API_KEY', '')
settings['API_URL'] = os.environ.get('API_URL', 'http://localhost:8989')
settings['API_TIMEOUT'] = int(os.environ.get('API_TIMEOUT', '60'))
settings['MONITORED_ONLY'] = os.environ.get('MONITORED_ONLY', 'true').lower() == 'true'
settings['HUNT_MISSING_SHOWS'] = int(os.environ.get('HUNT_MISSING_SHOWS', '1'))
settings['HUNT_UPGRADE_EPISODES'] = int(os.environ.get('HUNT_UPGRADE_EPISODES', '0'))
settings['SLEEP_SECONDS'] = int(os.environ.get('SLEEP_SECONDS', '1800'))
settings['STATE_RESET_HOURS'] = int(os.environ.get('STATE_RESET_HOURS', '168'))
settings['RANDOM_MISSING'] = os.environ.get('RANDOM_MISSING', 'true').lower() == 'true'
settings['RANDOM_UPGRADES'] = os.environ.get('RANDOM_UPGRADES', 'true').lower() == 'true'
settings['SKIP_FUTURE_EPISODES'] = os.environ.get('SKIP_FUTURE_EPISODES', 'true').lower() == 'true'
settings['SKIP_SERIES_REFRESH'] = os.environ.get('SKIP_SERIES_REFRESH', 'true').lower() == 'true'
settings['COMMAND_WAIT_SECONDS'] = int(os.environ.get('COMMAND_WAIT_SECONDS', '1'))
settings['COMMAND_WAIT_ATTEMPTS'] = int(os.environ.get('COMMAND_WAIT_ATTEMPTS', '600'))
settings['MINIMUM_DOWNLOAD_QUEUE_SIZE'] = int(os.environ.get('MINIMUM_DOWNLOAD_QUEUE_SIZE', '-1'))
settings['LOG_EPISODE_ERRORS'] = os.environ.get('LOG_EPISODE_ERRORS', 'false').lower() == 'true'
settings['DEBUG_API_CALLS'] = os.environ.get('DEBUG_API_CALLS', 'false').lower() == 'true'


def validate_config():
    """Validate that required configuration is set."""
    if not os.environ.get('API_KEY'):
        logger.error("API_KEY environment variable is required but not set")
        return False

    if not os.environ.get('API_URL'):
        logger.error("API_URL environment variable is required but not set")
        return False

    return True


def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global running
    logger.info("Received termination signal, shutting down...")
    running = False


def display_config():
    """Display the current configuration."""

    logger.info("=== Huntarr-Sonarr Configuration ===")
    for key, value in settings:
        # Don't log the API key
        if key != 'API_KEY':
            logger.info(f"{key}: {value}")
    logger.info("==================================")
