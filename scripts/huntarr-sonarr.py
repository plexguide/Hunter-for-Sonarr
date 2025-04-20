#!/usr/bin/env python3
import os
import time
import logging
import sys
import signal
import api
import state
import missing
import upgrade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('huntarr-sonarr')

# Get environment variables for configuration
SLEEP_SECONDS = int(os.environ.get('SLEEP_SECONDS', 1500))
COMMAND_WAIT_ATTEMPTS = int(os.environ.get('COMMAND_WAIT_ATTEMPTS', 600))

# Global flag to control execution
running = True

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
    config = {
        'API_URL': os.environ.get('API_URL'),
        'API_TIMEOUT': os.environ.get('API_TIMEOUT'),
        'MONITORED_ONLY': os.environ.get('MONITORED_ONLY'),
        'HUNT_MISSING_SHOWS': os.environ.get('HUNT_MISSING_SHOWS'),
        'HUNT_UPGRADE_EPISODES': os.environ.get('HUNT_UPGRADE_EPISODES'),
        'SLEEP_SECONDS': os.environ.get('SLEEP_SECONDS'),
        'STATE_RESET_HOURS': os.environ.get('STATE_RESET_HOURS'),
        'RANDOM_MISSING': os.environ.get('RANDOM_MISSING'),
        'RANDOM_UPGRADES': os.environ.get('RANDOM_UPGRADES'),
        'SKIP_FUTURE_EPISODES': os.environ.get('SKIP_FUTURE_EPISODES'),
        'SKIP_SERIES_REFRESH': os.environ.get('SKIP_SERIES_REFRESH'),
        'COMMAND_WAIT_SECONDS': os.environ.get('COMMAND_WAIT_SECONDS'),
        'COMMAND_WAIT_ATTEMPTS': os.environ.get('COMMAND_WAIT_ATTEMPTS'),
        'MINIMUM_DOWNLOAD_QUEUE_SIZE': os.environ.get('MINIMUM_DOWNLOAD_QUEUE_SIZE')
    }
    
    logger.info("=== Huntarr-Sonarr Configuration ===")
    for key, value in config.items():
        # Don't log the API key
        if key != 'API_KEY':
            logger.info(f"{key}: {value}")
    logger.info("==================================")

def main():
    """Main function to run the Huntarr-Sonarr application."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Huntarr-Sonarr")
    
    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration, exiting")
        sys.exit(1)
    
    # Display configuration
    display_config()
    
    # Initialize state
    state.ensure_state_dir()
    
    # Check API connection
    if not api.check_api_connection():
        logger.error("Could not connect to Sonarr API, exiting")
        sys.exit(1)
    
    try:
        cycle_count = 0
        # Main loop
        while running:
            cycle_count += 1
            logger.info(f"Starting cycle {cycle_count}")
            
            try:
                # Clean expired state
                state.clean_expired_state()
                
                # Process missing shows with the new optimized approach
                missing.process_missing_shows()
                
                # Process upgradable episodes
                upgrade.process_upgradable_episodes()
                
                # Sleep between cycles
                if running:
                    logger.info(f"Cycle {cycle_count} completed, sleeping for {SLEEP_SECONDS} seconds")
                    for _ in range(SLEEP_SECONDS):
                        if not running:
                            break
                        time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error during cycle {cycle_count}: {e}")
                # Sleep a bit before retrying
                time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    
    logger.info("Huntarr-Sonarr shutting down")

if __name__ == "__main__":
    main()