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
API_PAGE_SIZE = 100  # Number of episodes to fetch per page

def get_total_upgradable_count():
    """Get the total count of upgradable episodes to determine page range."""
    # Make a simple API call to get just the first record and total count
    result = api.get_quality_upgradable_episodes(1, 1)
    if not result or 'totalRecords' not in result:
        logger.error("Failed to retrieve total upgradable episode count")
        return 0
    
    total_records = result.get('totalRecords', 0)
    logger.info(f"Total upgradable episodes: {total_records}")
    return total_records

def find_random_upgradable_episode():
    """Find a single random episode that needs quality upgrade."""
    total_records = get_total_upgradable_count()
    if total_records == 0:
        logger.info("No upgradable episodes found")
        return None
    
    # Calculate how many pages exist
    total_pages = (total_records + API_PAGE_SIZE - 1) // API_PAGE_SIZE
    
    # Try up to 5 times to find a suitable episode
    for attempt in range(5):
        # Select a random page
        random_page = random.randint(1, total_pages)
        logger.info(f"Fetching random page {random_page} of {total_pages}")
        
        # Get episodes from the random page
        result = api.get_quality_upgradable_episodes(random_page, API_PAGE_SIZE)
        if not result or 'records' not in result:
            logger.error(f"Failed to retrieve page {random_page}")
            continue
        
        records = result.get('records', [])
        if not records:
            logger.warning(f"No records on page {random_page}")
            continue
        
        # Filter records to find monitored episodes
        valid_episodes = []
        for record in records:
            # Extract basic episode info for logging
            episode_id = record.get('id')
            season = record.get('seasonNumber')
            ep_num = record.get('episodeNumber')
            title = record.get('title')
            series_id = record.get('seriesId')
            
            # Skip episodes without required fields
            if not all([episode_id, series_id, season is not None, ep_num is not None]):
                continue
                
            # Skip unmonitored episodes if MONITORED_ONLY is True
            if MONITORED_ONLY and not record.get('monitored', False):
                continue
            
            # Skip episodes with future air dates if enabled
            if SKIP_FUTURE_EPISODES and api.is_date_in_future(record.get('airDateUtc')):
                continue
            
            # Get series info for this episode
            series = api.get_series_by_id(series_id)
            if not series:
                logger.warning(f"Could not get series info for episode ID {episode_id}")
                continue
            
            # Skip unmonitored series if MONITORED_ONLY is True
            if MONITORED_ONLY and not series.get('monitored', False):
                continue
                
            # This is a valid episode
            valid_episodes.append((record, series))
        
        if valid_episodes:
            # Select a random episode from the valid ones
            selected = random.choice(valid_episodes)
            logger.info(f"Found valid upgradable episode: {selected[1]['title']} - S{selected[0]['seasonNumber']:02d}E{selected[0]['episodeNumber']:02d}")
            return selected
    
    logger.info("Could not find a suitable upgradable episode after multiple attempts")
    return None

def find_episodes_needing_upgrade():
    """Find episodes that need quality upgrades."""
    logger.info("Searching for episodes that need quality upgrades...")
    
    # If using random selection and only need one episode, use the optimized method
    if RANDOM_UPGRADES and HUNT_UPGRADE_EPISODES == 1:
        episode_and_series = find_random_upgradable_episode()
        return [episode_and_series] if episode_and_series else []
    
    # For multiple episodes or sequential processing, we need to get all episodes
    # Get the first page to determine total records
    total_records = get_total_upgradable_count()
    if total_records == 0:
        return []
    
    # If using random selection and need multiple episodes, we'll fetch random pages
    if RANDOM_UPGRADES and HUNT_UPGRADE_EPISODES > 1:
        all_upgradable_episodes = []
        episodes_needed = min(HUNT_UPGRADE_EPISODES * 3, total_records)  # Fetch 3x to ensure we have enough after filtering
        
        # Calculate how many pages exist
        total_pages = (total_records + API_PAGE_SIZE - 1) // API_PAGE_SIZE
        
        # Generate a list of random pages without duplicates
        pages_to_fetch = min(total_pages, (episodes_needed + API_PAGE_SIZE - 1) // API_PAGE_SIZE)
        random_pages = random.sample(range(1, total_pages + 1), min(pages_to_fetch, total_pages))
        
        for page in random_pages:
            logger.info(f"Fetching page {page} of {total_pages}")
            result = api.get_quality_upgradable_episodes(page, API_PAGE_SIZE)
            
            if not result or 'records' not in result:
                logger.error(f"Failed to retrieve page {page}")
                continue
            
            records = result.get('records', [])
            
            # Process records on this page
            for record in records:
                # Get basic info
                episode_id = record.get('id')
                series_id = record.get('seriesId')
                
                # Skip episodes without required fields
                if not all([episode_id, series_id]):
                    continue
                
                # Skip unmonitored episodes if MONITORED_ONLY is True
                if MONITORED_ONLY and not record.get('monitored', False):
                    continue
                
                # Skip episodes with future air dates if enabled
                if SKIP_FUTURE_EPISODES and api.is_date_in_future(record.get('airDateUtc')):
                    continue
                
                # Get series info for this episode
                series = api.get_series_by_id(series_id)
                if not series:
                    logger.warning(f"Could not get series info for episode ID {episode_id}")
                    continue
                
                # Skip unmonitored series if MONITORED_ONLY is True
                if MONITORED_ONLY and not series.get('monitored', False):
                    continue
                
                # Add to our upgradable episodes list
                all_upgradable_episodes.append((record, series))
            
            # If we've found enough episodes, stop fetching more pages
            if len(all_upgradable_episodes) >= episodes_needed:
                break
        
        # Shuffle the final list for true randomness
        random.shuffle(all_upgradable_episodes)
        
    else:
        # Sequential processing - fetch pages in order
        all_upgradable_episodes = []
        page = 1
        
        while True:
            logger.info(f"Fetching page {page} of upgradable episodes")
            result = api.get_quality_upgradable_episodes(page, API_PAGE_SIZE)
            
            if not result:
                logger.error("Failed to retrieve quality upgrades")
                break
            
            records = result.get('records', [])
            if not records:
                logger.info(f"No more records found on page {page}")
                break
            
            logger.info(f"Processing {len(records)} records from page {page}")
            
            for record in records:
                # Get basic info
                episode_id = record.get('id')
                series_id = record.get('seriesId')
                
                # Skip episodes without required fields
                if not all([episode_id, series_id]):
                    continue
                
                # Skip unmonitored episodes if MONITORED_ONLY is True
                if MONITORED_ONLY and not record.get('monitored', False):
                    continue
                
                # Skip episodes with future air dates if enabled
                if SKIP_FUTURE_EPISODES and api.is_date_in_future(record.get('airDateUtc')):
                    continue
                
                # Get series info for this episode
                series = api.get_series_by_id(series_id)
                if not series:
                    logger.warning(f"Could not get series info for episode ID {episode_id}")
                    continue
                
                # Skip unmonitored series if MONITORED_ONLY is True
                if MONITORED_ONLY and not series.get('monitored', False):
                    continue
                
                # Add to our upgradable episodes list
                all_upgradable_episodes.append((record, series))
            
            # Check if we've reached the last page
            if page * API_PAGE_SIZE >= total_records:
                logger.debug(f"Reached end of upgradable episodes ({total_records} total)")
                break
            
            page += 1
    
    logger.info(f"Found {len(all_upgradable_episodes)} episodes that need quality upgrades")
    return all_upgradable_episodes

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
    
    logger.info(f"Beginning search for episodes needing quality upgrades (max {HUNT_UPGRADE_EPISODES})")
    
    # Find episodes that need quality upgrades
    upgradable_episodes = find_episodes_needing_upgrade()
    if not upgradable_episodes:
        logger.info("No episodes found that need quality upgrades")
        return
    
    # Filter out episodes that have already been processed
    episodes_to_process = [(episode, series) for episode, series in upgradable_episodes
                          if not state.is_episode_processed(episode['id'])]
    
    logger.info(f"Found {len(upgradable_episodes)} total upgradable episodes, {len(episodes_to_process)} not yet processed")
    
    if not episodes_to_process:
        logger.info("All episodes needing quality upgrades have been processed recently")
        return
    
    # Process up to HUNT_UPGRADE_EPISODES
    episodes_count = min(HUNT_UPGRADE_EPISODES, len(episodes_to_process))
    episodes_to_process = episodes_to_process[:episodes_count]
    logger.info(f"Will process {episodes_count} episodes for quality upgrades")
    
    for idx, (episode, series) in enumerate(episodes_to_process, 1):
        episode_info = f"S{episode.get('seasonNumber', 0):02d}E{episode.get('episodeNumber', 0):02d}"
        logger.info(f"[{idx}/{episodes_count}] Searching for upgrade for {series['title']} - {episode_info}: {episode.get('title')}")
        
        # Search for episode
        search_result = api.search_for_episode(episode['id'])
        
        if search_result:
            logger.info(f"Search initiated successfully for episode ID {episode['id']}")
            # Mark episode as processed
            state.mark_episode_processed(episode['id'])
        else:
            logger.warning(f"Search failed for episode ID {episode['id']}")
        
        # Wait between API calls
        time.sleep(COMMAND_WAIT_SECONDS)