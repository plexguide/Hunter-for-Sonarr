#!/usr/bin/env python3
import os
from src.utils.logger import logger
from src.schema.settings import Settings
'''TODO add a function here that starts the FLask / api app'''
"""
Huntarr-Sonarr - Automatically search for missing episodes and episode upgrades
"""


settings = Settings()


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
    for key, value in settings.model_dump().items():
        # Don't log the API key
        if key != 'API_KEY':
            logger.info(f"{key}: {value}")
    logger.info("==================================")
