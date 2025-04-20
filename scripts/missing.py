#!/usr/bin/env python3
import os
import random
import logging
import time
from datetime import datetime
import api
import state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('huntarr-sonarr')

# Get environment variables
MONITORED_ONLY = os.environ.get('MONITORED_ONLY', 'true').lower() == 'true'
RANDOM_MISSING = os.environ.get('RANDOM_MISSING', 'true').lower() == 'true'
SKIP_FUTURE_EPISODES = os.environ.get('SKIP_FUTURE_EPISODES', 'true').lower() == 'true'
SKIP_SERIES_REFRESH = os.environ.get('SKIP_SERIES_REFRESH', 'true').lower() == 'true'
COMMAND_WAIT_SECONDS = int(os.environ.get('COMMAND_WAIT_SECONDS', 1))
MINIMUM_DOWNLOAD_QUEUE_SIZE = int(os.environ.get('MINIMUM_DOWNLOAD_QUEUE_SIZE', -1))
HUNT_MISSING_SHOWS = int(os.environ.get('HUNT_MISSING_SHOWS', 1))

def get_shows_with_missing_episodes():
    """Get a list of shows that have missing episodes."""
    all_series = api.get_series()
    if not all_series:
        logger.error("Failed to retrieve series from Sonarr")
        return []
    
    shows_with_missing = []
    
    logger.info(f"Found {len(all_series)} series in Sonarr")
    
    for series in all_series:
        # Skip unmonitored series if MONITORED_ONLY is True
        if MONITORED_ONLY and not series.get('monitored', False):
            continue
        
        # Get episodes for this series
        episodes = api.get_episodes_by_series_id(series['id'])
        if not episodes:
            logger.error(f"Failed to retrieve episodes for series '{series['title']}'")
            continue
        
        # Count missing episodes
        missing_count = 0
        for episode in episodes:
            if episode.get('monitored', False) and not episode.get('hasFile', False):
                # Skip episodes with future air dates if enabled
                if SKIP_FUTURE_EPISODES and api.is_date_in_future(episode.get('airDateUtc')):
                    continue
                missing_count += 1
        
        if missing_count > 0:
            logger.debug(f"Series '{series['title']}' has {missing_count} missing episodes")
            shows_with_missing.append((series, missing_count))
    
    logger.info(f"Found {len(shows_with_missing)} series with missing episodes")
    return shows_with_missing

def check_download_queue():
    """Check if we should proceed based on download queue size."""
    if MINIMUM_DOWNLOAD_QUEUE_SIZE < 0:
        return True
    
    queue_size = api.get_queue_size()
    logger.info(f"Current download queue size: {queue_size}")
    
    return queue_size <= MINIMUM_DOWNLOAD_QUEUE_SIZE

def process_missing_shows():
    """Process shows with missing episodes."""
    # If HUNT_MISSING_SHOWS is 0, skip this function
    if HUNT_MISSING_SHOWS <= 0:
        logger.info("Skipping hunt for missing shows (HUNT_MISSING_SHOWS is 0)")
        return

    # Check download queue
    if not check_download_queue():
        logger.info("Download queue is too large, skipping search for missing episodes")
        return
    
    # Get shows with missing episodes
    shows_with_missing = get_shows_with_missing_episodes()
    if not shows_with_missing:
        logger.info("No shows with missing episodes found")
        return
    
    # Filter out shows that have already been processed
    shows_to_process = [(series, count) for series, count in shows_with_missing 
                        if not state.is_show_processed(series['id'])]
    
    if not shows_to_process:
        logger.info("All shows with missing episodes have been processed recently")
        return
    
    logger.info(f"{len(shows_to_process)} shows with missing episodes available to process")
    
    # Sort or randomize shows
    if RANDOM_MISSING:
        random.shuffle(shows_to_process)
    else:
        # Sort by most missing episodes
        shows_to_process.sort(key=lambda x: x[1], reverse=True)
    
    # Process up to HUNT_MISSING_SHOWS
    shows_to_process = shows_to_process[:HUNT_MISSING_SHOWS]
    
    for series, missing_count in shows_to_process:
        logger.info(f"Processing series '{series['title']}' with {missing_count} missing episodes")
        
        # Refresh series metadata if needed
        if not SKIP_SERIES_REFRESH:
            logger.info(f"Refreshing metadata for '{series['title']}'")
            api.refresh_series(series['id'])
            time.sleep(COMMAND_WAIT_SECONDS)
        
        # Search for missing episodes
        api.search_for_series(series['id'])
        
        # Mark show as processed
        state.mark_show_processed(series['id'])
        
        # Wait between API calls
        time.sleep(COMMAND_WAIT_SECONDS)