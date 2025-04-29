#!/usr/bin/env python3
"""
Sonarr missing episodes processing module for Huntarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.sonarr import api as sonarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

def process_missing_episodes(
    api_url: str,
    api_key: str,
    api_timeout: int = 60,
    monitored_only: bool = True,
    skip_future_episodes: bool = True,
    skip_series_refresh: bool = False,
    random_missing: bool = False,
    hunt_missing_items: int = 5,
    hunt_missing_mode: str = "episodes",
    command_wait_delay: int = 5,
    command_wait_attempts: int = 10,
    stop_check: Callable[[], bool] = lambda: False
) -> bool:
    """
    Process missing episodes in Sonarr and trigger searches
    Added support for multiple missing modes (episodes, seasons, shows)
    """
    if hunt_missing_items <= 0:
        sonarr_logger.info("'hunt_missing_items' setting is 0 or less. Skipping missing processing.")
        return False
        
    sonarr_logger.info(f"Checking for {hunt_missing_items} missing episodes in {hunt_missing_mode} mode...")

    # Handle different modes
    if hunt_missing_mode == "episodes":
        # Handle episode-based missing items
        sonarr_logger.info("Episode-based missing mode selected")
        return process_missing_episodes_mode(
            api_url, api_key, api_timeout, monitored_only, 
            skip_future_episodes, skip_series_refresh, random_missing,
            hunt_missing_items, command_wait_delay, command_wait_attempts,
            stop_check
        )
    elif hunt_missing_mode == "seasons":
        # Handle season-based missing items (individual episodes grouped by season)
        sonarr_logger.info("Season [Solo] mode selected - grouping episodes by season")
        return process_missing_seasons_mode(
            api_url, api_key, api_timeout, monitored_only, 
            skip_series_refresh, random_missing, hunt_missing_items,
            command_wait_delay, command_wait_attempts, stop_check
        )
    elif hunt_missing_mode == "seasons_packs":
        # Handle season pack searches (using SeasonSearch command)
        sonarr_logger.info("Season [Packs] mode selected - searching for complete season packs")
        return process_missing_seasons_packs_mode(
            api_url, api_key, api_timeout, monitored_only, 
            skip_series_refresh, random_missing, hunt_missing_items,
            command_wait_delay, command_wait_attempts, stop_check
        )
    elif hunt_missing_mode == "shows":
        # Handle show-based missing items
        sonarr_logger.info("Show-based missing mode selected")
        return process_missing_shows_mode(
            api_url, api_key, api_timeout, monitored_only, 
            skip_future_episodes, skip_series_refresh, random_missing,
            hunt_missing_items, command_wait_delay, command_wait_attempts,
            stop_check
        )
    else:
        sonarr_logger.error(f"Invalid hunt_missing_mode: {hunt_missing_mode}. Valid options are 'episodes', 'seasons', 'seasons_packs', or 'shows'.")
        return False

def process_missing_episodes_mode(
    api_url: str,
    api_key: str,
    api_timeout: int,
    monitored_only: bool,
    skip_future_episodes: bool,
    skip_series_refresh: bool,
    random_missing: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process missing episodes in episode mode (original implementation)."""
    processed_any = False
    
    # Use different methods based on random setting
    episodes_to_search = []
    
    if random_missing:
        # Use the efficient random page selection method
        sonarr_logger.info(f"Using random selection for missing episodes")
        episodes_to_search = sonarr_api.get_missing_episodes_random_page(
            api_url, api_key, api_timeout, monitored_only, hunt_missing_items)
    else:
        # Use the sequential approach for non-random selection
        sonarr_logger.info(f"Using sequential selection for missing episodes (oldest first)")
        missing_episodes = sonarr_api.get_missing_episodes(api_url, api_key, api_timeout, monitored_only)
        sonarr_logger.info(f"Received {len(missing_episodes)} missing episodes from Sonarr API (before filtering).")
        
        if not missing_episodes:
            sonarr_logger.info("No missing episodes found in Sonarr.")
            return False
            
        # Filter out future episodes if configured
        if skip_future_episodes:
            now_unix = time.time()
            original_count = len(missing_episodes)
            # Ensure airDateUtc exists and is not None before parsing
            missing_episodes = [
                ep for ep in missing_episodes
                if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
            ]
            skipped_count = original_count - len(missing_episodes)
            if skipped_count > 0:
                sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date.")
                
        # Select the first N episodes
        episodes_to_search = missing_episodes[:hunt_missing_items]

    if stop_check(): 
        sonarr_logger.info("Stop requested during missing episode processing.")
        return processed_any
        
    # Filter out future episodes for random selection approach
    if random_missing and skip_future_episodes:
        now_unix = time.time()
        original_count = len(episodes_to_search)
        episodes_to_search = [
            ep for ep in episodes_to_search
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(episodes_to_search)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date.")

    if not episodes_to_search:
        sonarr_logger.info("No missing episodes left to process after filtering.")
        return False

    sonarr_logger.info(f"Selected {len(episodes_to_search)} missing episodes to search.")
    
    # Add detailed listing of episodes being processed
    if episodes_to_search:
        sonarr_logger.info(f"Episodes selected for processing in this cycle:")
        for idx, episode in enumerate(episodes_to_search):
            series_title = episode.get('series', {}).get('title', 'Unknown Series')
            episode_title = episode.get('title', 'Unknown Episode')
            season_number = episode.get('seasonNumber', 'Unknown Season')
            episode_number = episode.get('episodeNumber', 'Unknown Episode')
                
            episode_id = episode.get("id")
            try:
                season_episode = f"S{season_number:02d}E{episode_number:02d}"
            except (ValueError, TypeError):
                season_episode = f"S{season_number}E{episode_number}"
                
            sonarr_logger.info(f" {idx+1}. {series_title} - {season_episode} - \"{episode_title}\" (ID: {episode_id})")
    
    # Group episodes by series for potential refresh
    series_to_refresh: Dict[int, List[int]] = {}
    series_titles: Dict[int, str] = {} # Store titles for logging
    for episode in episodes_to_search:
        series_id = episode.get('seriesId')
        if series_id:
            if series_id not in series_to_refresh:
                series_to_refresh[series_id] = []
                # Store title when first encountering the series ID
                series_titles[series_id] = episode.get('series', {}).get('title', f"Series ID {series_id}")
            series_to_refresh[series_id].append(episode['id'])

    # Process each series
    for series_id, episode_ids in series_to_refresh.items():
        if stop_check(): sonarr_logger.info("Stop requested before processing next series."); break
        series_title = series_titles.get(series_id, f"Series ID {series_id}")
        sonarr_logger.info(f"Processing series: {series_title} (ID: {series_id}) with {len(episode_ids)} missing episodes.")

        # Refresh series metadata if not skipped
        refresh_command_id = None
        if not skip_series_refresh:
            sonarr_logger.debug(f"Attempting to refresh series ID: {series_id}")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                # Wait for refresh command to complete
                if not wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh", stop_check
                ):
                    sonarr_logger.warning(f"Series refresh command (ID: {refresh_command_id}) for series {series_id} did not complete successfully or timed out. Proceeding with search anyway.")
            else:
                 sonarr_logger.warning(f"Failed to trigger refresh command for series ID: {series_id}. Proceeding without refresh.")
        else:
            sonarr_logger.debug(f"Skipping series refresh for series ID: {series_id} as configured.")

        if stop_check(): sonarr_logger.info("Stop requested after series refresh attempt."); break

        # Trigger search for the selected episodes in this series
        sonarr_logger.debug(f"Attempting to search for episode IDs: {episode_ids}")
        search_command_id = sonarr_api.search_episode(api_url, api_key, api_timeout, episode_ids)

        if search_command_id:
            # Wait for search command to complete
            if wait_for_command(
                api_url, api_key, api_timeout, search_command_id,
                command_wait_delay, command_wait_attempts, "Episode Search", stop_check
            ):
                # Mark episodes as processed if search command completed successfully
                processed_any = True # Mark that we did something
                sonarr_logger.info(f"Successfully processed and searched for {len(episode_ids)} episodes in series {series_id}.")
                
                # Increment the hunted statistics
                increment_stat("sonarr", "hunted", len(episode_ids))
                sonarr_logger.debug(f"Incremented sonarr hunted statistics by {len(episode_ids)}")
            else:
                sonarr_logger.warning(f"Episode search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed yet.")
        else:
            sonarr_logger.error(f"Failed to trigger search command for episodes {episode_ids} in series {series_id}.")

    sonarr_logger.info("Finished missing episodes processing cycle for Sonarr.")
    return processed_any

def process_missing_seasons_mode(
    api_url: str,
    api_key: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
    random_missing: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """
    Process missing seasons using season pack search
    This mode uses the SeasonSearch command to search for entire season packs instead of individual episodes
    """
    processed_any = False
    
    series = sonarr_api.get_series(api_url, api_key, api_timeout)
    if not series:
        sonarr_logger.error("Failed to retrieve series list for processing missing seasons")
        return False
    
    # Group episodes by series and season
    missing_seasons = {}
    for show in series:
        if monitored_only and not show.get('monitored', False):
            continue
            
        series_id = show.get('id')
        if not series_id:
            continue
            
        # Get all missing episodes for this series
        series_missing = sonarr_api.get_missing_episodes(api_url, api_key, api_timeout, monitored_only=monitored_only, series_id=series_id)
        
        # Group by season number
        for episode in series_missing:
            if monitored_only and not episode.get('monitored', False):
                continue
                
            season_number = episode.get('seasonNumber')
            series_title = show.get('title', 'Unknown Series')
            
            key = f"{series_id}:{season_number}"
            if key not in missing_seasons:
                missing_seasons[key] = {
                    'series_id': series_id,
                    'season_number': season_number,
                    'series_title': series_title,
                    'episode_count': 0
                }
            missing_seasons[key]['episode_count'] += 1
    
    # Convert to list and sort by episode count (most missing episodes first)
    seasons_list = list(missing_seasons.values())
    seasons_list.sort(key=lambda x: x['episode_count'], reverse=True)
    
    # Apply randomization if requested
    if random_missing:
        random.shuffle(seasons_list)
    
    # Process up to hunt_missing_items seasons
    processed_count = 0
    for season in seasons_list:
        if processed_count >= hunt_missing_items:
            break
            
        if stop_check():
            sonarr_logger.info("Stop signal received, halting processing.")
            break
            
        series_id = season['series_id']
        season_number = season['season_number']
        series_title = season['series_title']
        episode_count = season['episode_count']
        
        sonarr_logger.info(f"Searching for season pack: {series_title} - Season {season_number} (contains {episode_count} missing episodes)")
        
        # Trigger an API call to search for the entire season
        command_id = sonarr_api.search_season(api_url, api_key, api_timeout, series_id, season_number)
        
        if command_id:
            processed_any = True
            processed_count += 1
            
            # Wait for command to complete if configured
            if command_wait_delay > 0 and command_wait_attempts > 0:
                wait_for_command(
                    api_url, api_key, api_timeout, command_id, 
                    command_wait_delay, command_wait_attempts, "Season Search", stop_check
                )
    
    sonarr_logger.info(f"Processed {processed_count} missing season packs for Sonarr.")
    return processed_any

def process_missing_seasons_packs_mode(
    api_url: str,
    api_key: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
    random_missing: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """
    Process missing seasons using the SeasonSearch command
    This mode is optimized for torrent users who rely on season packs
    Uses a direct episode lookup approach which is much more efficient
    """
    processed_any = False
    
    sonarr_logger.info("Running Season [Packs] mode with optimized performance for large libraries")
    
    # Use our new optimized function to get series with missing episodes
    series_with_missing = sonarr_api.get_series_with_missing_episodes(
        api_url, api_key, api_timeout, 
        monitored_only=monitored_only, 
        limit=50,  # Examine at most 50 series for performance
        random_mode=random_missing
    )
    
    if not series_with_missing:
        sonarr_logger.info("No series with missing episodes found")
        return False
    
    # Convert to a flat list of seasons with missing episodes
    missing_seasons = []
    for series in series_with_missing:
        series_id = series['series_id']
        series_title = series['series_title']
        
        for season in series['seasons']:
            missing_seasons.append({
                'series_id': series_id,
                'season_number': season['season_number'],
                'series_title': series_title,
                'episode_count': season['episode_count']
            })
    
    # Sort by episode count (most missing episodes first)
    missing_seasons.sort(key=lambda x: x['episode_count'], reverse=True)
    
    # No need to shuffle again, as we already shuffled at the series selection level if random mode is on
    
    sonarr_logger.info(f"Found {len(missing_seasons)} seasons with missing episodes across {len(series_with_missing)} series")
    
    # Process up to hunt_missing_items seasons
    processed_count = 0
    for season in missing_seasons[:hunt_missing_items]:
        if processed_count >= hunt_missing_items:
            break
            
        if stop_check():
            sonarr_logger.info("Stop signal received, halting processing.")
            break
            
        series_id = season['series_id']
        season_number = season['season_number']
        series_title = season['series_title']
        episode_count = season['episode_count']
        
        # Refresh series metadata if not skipped
        if not skip_series_refresh:
            sonarr_logger.debug(f"Refreshing metadata for {series_title} before season pack search")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh", stop_check
                )
        
        sonarr_logger.info(f"Searching for season pack: {series_title} - Season {season_number} (contains {episode_count} missing episodes)")
        
        # Trigger an API call to search for the entire season
        command_id = sonarr_api.search_season(api_url, api_key, api_timeout, series_id, season_number)
        
        if command_id:
            processed_any = True
            processed_count += 1
            
            # Wait for command to complete if configured
            if command_wait_delay > 0 and command_wait_attempts > 0:
                if wait_for_command(
                    api_url, api_key, api_timeout, command_id, 
                    command_wait_delay, command_wait_attempts, "Season Pack Search", stop_check
                ):
                    # Increment stats by the number of episodes in the season
                    increment_stat("sonarr", "hunted", episode_count)
                    sonarr_logger.debug(f"Incremented sonarr hunted statistics by {episode_count} (full season)")
    
    sonarr_logger.info(f"Processed {processed_count} missing season packs for Sonarr.")
    return processed_any

def process_missing_shows_mode(
    api_url: str,
    api_key: str,
    api_timeout: int,
    monitored_only: bool,
    skip_future_episodes: bool,
    skip_series_refresh: bool,
    random_missing: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process missing episodes in show mode - gets all missing episodes for entire shows."""
    processed_any = False
    
    # Get all missing episodes
    missing_episodes = sonarr_api.get_missing_episodes(api_url, api_key, api_timeout, monitored_only)
    sonarr_logger.info(f"Received {len(missing_episodes)} missing episodes from Sonarr API (before filtering).")
    
    if not missing_episodes:
        sonarr_logger.info("No missing episodes found in Sonarr.")
        return False
        
    # Filter out future episodes if configured
    if skip_future_episodes:
        now_unix = time.time()
        original_count = len(missing_episodes)
        # Ensure airDateUtc exists and is not None before parsing
        missing_episodes = [
            ep for ep in missing_episodes
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(missing_episodes)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date.")
    
    if stop_check(): 
        sonarr_logger.info("Stop requested during missing episode processing.")
        return processed_any
    
    # Group episodes by series
    series_episodes: Dict[int, List[Dict]] = {}
    series_titles: Dict[int, str] = {}  # Keep track of series titles
    
    for episode in missing_episodes:
        series_id = episode.get('seriesId')
        if series_id is not None:
            if series_id not in series_episodes:
                series_episodes[series_id] = []
                # Store series title when first encountering the series ID
                series_titles[series_id] = episode.get('series', {}).get('title', f"Series ID {series_id}")
            
            series_episodes[series_id].append(episode)
    
    # Create a list of (series_id, episode_count, series_title) tuples for selection
    available_series = [(series_id, len(episodes), series_titles[series_id]) 
                         for series_id, episodes in series_episodes.items()]
    
    if not available_series:
        sonarr_logger.info("No series with missing episodes found.")
        return False
    
    # Select series to process - either randomly or sequentially
    series_to_process = []
    if random_missing:
        # Randomly shuffle the available series
        random.shuffle(available_series)
        series_to_process = available_series[:hunt_missing_items]
    else:
        # Sort by missing episode count (descending) for most impactful processing
        available_series.sort(key=lambda x: x[1], reverse=True)
        series_to_process = available_series[:hunt_missing_items]
    
    sonarr_logger.info(f"Selected {len(series_to_process)} series with missing episodes to process")
    
    # Log selected series
    for idx, (series_id, episode_count, series_title) in enumerate(series_to_process):
        sonarr_logger.info(f" {idx+1}. {series_title} - {episode_count} missing episodes")
    
    # Process each selected series
    for series_id, _, series_title in series_to_process:
        if stop_check(): 
            sonarr_logger.info("Stop requested before processing next series.")
            break
            
        episodes = series_episodes[series_id]
        episode_ids = [episode["id"] for episode in episodes]
        
        sonarr_logger.info(f"Processing {series_title} with {len(episode_ids)} missing episodes")
        
        # Refresh series metadata if not skipped
        if not skip_series_refresh:
            sonarr_logger.debug(f"Attempting to refresh series ID: {series_id}")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                # Wait for refresh command to complete
                if not wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh", stop_check
                ):
                    sonarr_logger.warning(f"Series refresh command for {series_title} did not complete successfully or timed out.")
            else:
                sonarr_logger.warning(f"Failed to trigger refresh command for series {series_title}")
                
        if stop_check(): 
            sonarr_logger.info("Stop requested after series refresh attempt.")
            break
            
        # Trigger search for all missing episodes in this series
        sonarr_logger.debug(f"Attempting to search for {len(episode_ids)} episodes in {series_title}")
        search_command_id = sonarr_api.search_episode(api_url, api_key, api_timeout, episode_ids)
        
        if search_command_id:
            # Wait for search command to complete
            if wait_for_command(
                api_url, api_key, api_timeout, search_command_id,
                command_wait_delay, command_wait_attempts, "Episode Search", stop_check
            ):
                # Mark as processed if search command completed successfully
                processed_any = True
                sonarr_logger.info(f"Successfully processed {len(episode_ids)} missing episodes in {series_title}")
                
                # Increment the hunted statistics
                increment_stat("sonarr", "hunted", len(episode_ids))
                sonarr_logger.debug(f"Incremented sonarr hunted statistics by {len(episode_ids)}")
            else:
                sonarr_logger.warning(f"Episode search command for {series_title} did not complete successfully")
        else:
            sonarr_logger.error(f"Failed to trigger search command for {series_title}")
    
    sonarr_logger.info("Finished missing episodes processing cycle (show mode) for Sonarr.")
    return processed_any

def wait_for_command(
    api_url: str,
    api_key: str,
    api_timeout: int,
    command_id: int,
    wait_delay: int,
    max_attempts: int,
    command_name: str = "Command",
    stop_check: Callable[[], bool] = lambda: False
) -> bool:
    """
    Wait for a Sonarr command to complete or timeout.
    
    Args:
        api_url: The Sonarr API URL
        api_key: The Sonarr API key
        api_timeout: API request timeout
        command_id: The ID of the command to monitor
        wait_delay: Seconds to wait between status checks
        max_attempts: Maximum number of status check attempts
        command_name: Name of the command (for logging)
        stop_check: Optional function to check if operation should be aborted
        
    Returns:
        True if command completed successfully, False otherwise
    """
    if wait_delay <= 0 or max_attempts <= 0:
        sonarr_logger.debug(f"Not waiting for command to complete (wait_delay={wait_delay}, max_attempts={max_attempts})")
        return True  # Return as if successful since we're not checking
    
    sonarr_logger.debug(f"Waiting for {command_name} to complete (command ID: {command_id}). Checking every {wait_delay}s for up to {max_attempts} attempts")
    
    # Wait for command completion
    for attempt in range(1, max_attempts + 1):
        if stop_check():
            sonarr_logger.info(f"Stopping wait for {command_name} due to stop request")
            return False
            
        # Adding a short initial delay before first check
        time.sleep(wait_delay)
        
        command_status = sonarr_api.get_command_status(api_url, api_key, api_timeout, command_id)
        if not command_status:
            sonarr_logger.warning(f"Failed to get status for {command_name} (ID: {command_id}), attempt {attempt}")
            continue
            
        status = command_status.get('status')
        if status == 'completed':
            sonarr_logger.debug(f"Sonarr {command_name} (ID: {command_id}) completed successfully")
            return True
        elif status in ['failed', 'aborted']:
            sonarr_logger.warning(f"Sonarr {command_name} (ID: {command_id}) {status}")
            return False
        
        sonarr_logger.debug(f"Sonarr {command_name} (ID: {command_id}) status: {status}, attempt {attempt}/{max_attempts}")
    
    sonarr_logger.error(f"Sonarr command '{command_name}' (ID: {command_id}) timed out after {max_attempts} attempts.")
    return False