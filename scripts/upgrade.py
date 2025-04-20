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
RANDOM_UPGRADES = os.environ.get('RANDOM_UPGRADES', 'true').lower() == 'true'
SKIP_FUTURE_EPISODES = os.environ.get('SKIP_FUTURE_EPISODES', 'true').lower() == 'true'
COMMAND_WAIT_SECONDS = int(os.environ.get('COMMAND_WAIT_SECONDS', 1))
MINIMUM_DOWNLOAD_QUEUE_SIZE = int(os.environ.get('MINIMUM_DOWNLOAD_QUEUE_SIZE', -1))
HUNT_UPGRADE_EPISODES = int(os.environ.get('HUNT_UPGRADE_EPISODES', 0))

def find_episodes_needing_upgrade():
    """Find episodes that need quality upgrades."""
    all_series = api.get_series()
    if not all_series:
        logger.error("Failed to retrieve series from Sonarr")
        return []
    
    upgradable_episodes = []
    
    for series in all_series:
        # Skip unmonitored series if MONITORED_ONLY is True
        if MONITORED_ONLY and not series.get('monitored', False):
            continue
        
        episodes = api.get_episodes_by_series_id(series['id'])
        if not episodes:
            continue
        
        for episode in episodes:
            # Skip unmonitored episodes
            if MONITORED_ONLY and not episode.get('monitored', False):
                continue
            
            # Skip episodes without files
            if not episode.get('hasFile', False):
                continue
            
            # Skip episodes with future air dates if configured
            if SKIP_FUTURE_EPISODES and api.is_date_in_future(episode.get('airDateUtc')):
                continue
            
            # Check if episode needs quality upgrade
            quality_cutoff_met = episode.get('qualityCutoffNotMet', False)
            if quality_cutoff_met:
                upgradable_episodes.append((episode, series))
    
    logger.info(f"Found {len(upgradable_episodes)} episodes that need quality upgrades")
    return upgradable_episodes

def check_download_queue():
    """Check if we should proceed based on download queue size."""
    if MINIMUM_DOWNLOAD_QUEUE_SIZE < 0:
        return True
    
    queue_size = api.get_queue_size()
    logger.info(f"Current download queue size: {queue_size}")
    
    return queue_size <= MINIMUM_DOWNLOAD_QUEUE_SIZE

def process_upgradable_episodes():
    """Process episodes that need quality upgrades."""
    # If HUNT_UPGRADE_EPISODES is 0, skip this function
    if HUNT_UPGRADE_EPISODES <= 0:
        logger.info("Skipping hunt for quality upgrades (HUNT_UPGRADE_EPISODES is 0)")
        return
    
    # Check download queue
    if not check_download_queue():
        logger.info("Download queue is too large, skipping search for quality upgrades")
        return
    
    # Find episodes that need quality upgrades
    upgradable_episodes = find_episodes_needing_upgrade()
    if not upgradable_episodes:
        logger.info("No episodes found that need quality upgrades")
        return
    
    # Filter out episodes that have already been processed
    episodes_to_process = [(episode, series) for episode, series in upgradable_episodes
                          if not state.is_episode_processed(episode['id'])]
    
    if not episodes_to_process:
        logger.info("All episodes needing quality upgrades have been processed recently")
        return
    
    logger.info(f"{len(episodes_to_process)} episodes that need quality upgrades available to process")
    
    # Sort or randomize episodes
    if RANDOM_UPGRADES:
        random.shuffle(episodes_to_process)
    else:
        # Sort by air date (oldest first)
        episodes_to_process.sort(key=lambda x: x[0].get('airDateUtc', ''), reverse=False)
    
    # Process up to HUNT_UPGRADE_EPISODES
    episodes_to_process = episodes_to_process[:HUNT_UPGRADE_EPISODES]
    
    for episode, series in episodes_to_process:
        episode_info = f"S{episode.get('seasonNumber', 0):02d}E{episode.get('episodeNumber', 0):02d}"
        logger.info(f"Searching for upgrade for {series['title']} - {episode_info}: {episode.get('title')}")
        
        # Search for episode
        api.search_for_episode(episode['id'])
        
        # Mark episode as processed
        state.mark_episode_processed(episode['id'])
        
        # Wait between API calls
        time.sleep(COMMAND_WAIT_SECONDS)