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
from src.primary.stateful_manager import is_processed, add_processed_id

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

def process_missing_episodes(
    api_url: str,
    api_key: str,
    instance_name: str = "Default",
    api_timeout: int = 60,
    monitored_only: bool = True,
    skip_future_episodes: bool = True,
    skip_series_refresh: bool = False,
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
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_future_episodes, skip_series_refresh,
            hunt_missing_items, command_wait_delay, command_wait_attempts,
            stop_check
        )
    elif hunt_missing_mode == "seasons_packs":
        # Handle season pack searches (using SeasonSearch command)
        sonarr_logger.info("Season [Packs] mode selected - searching for complete season packs")
        return process_missing_seasons_packs_mode(
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_series_refresh, hunt_missing_items,
            command_wait_delay, command_wait_attempts, stop_check
        )
    elif hunt_missing_mode == "shows":
        # Handle show-based missing items (all episodes from a show)
        sonarr_logger.info("Show-based missing mode selected")
        return process_missing_shows_mode(
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_future_episodes, skip_series_refresh, hunt_missing_items,
            command_wait_delay, command_wait_attempts, stop_check
        )
    else:
        sonarr_logger.error(f"Invalid hunt_missing_mode: {hunt_missing_mode}. Valid options are 'episodes', 'seasons_packs', or 'shows'.")
        return False

def process_missing_episodes_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_future_episodes: bool,
    skip_series_refresh: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process missing episodes in episode mode (original implementation)."""
    processed_any = False
    
    # Always use random selection for missing episodes
    sonarr_logger.info(f"Using random selection for missing episodes")
    episodes_to_search = sonarr_api.get_missing_episodes_random_page(
        api_url, api_key, api_timeout, monitored_only, hunt_missing_items)

    if stop_check(): 
        sonarr_logger.info("Stop requested during missing episode processing.")
        return processed_any
        
    # Filter out future episodes for random selection approach
    if skip_future_episodes:
        now_unix = time.time()
        original_count = len(episodes_to_search)
        episodes_to_search = [
            ep for ep in episodes_to_search
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(episodes_to_search)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date.")
    
    # Filter out already processed episodes for random selection approach
    unprocessed_episodes = []
    for episode in episodes_to_search:
        episode_id = str(episode.get("id"))
        if not is_processed("sonarr", instance_name, episode_id):
            unprocessed_episodes.append(episode)
        else:
            sonarr_logger.debug(f"Skipping already processed episode ID: {episode_id}")
    
    sonarr_logger.info(f"Found {len(unprocessed_episodes)} unprocessed missing episodes out of {len(episodes_to_search)} total.")
    episodes_to_search = unprocessed_episodes

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
                
                # Add episode IDs to stateful manager
                for episode_id in episode_ids:
                    add_processed_id("sonarr", instance_name, episode_id)
                
                # Increment the hunted statistics
                increment_stat("sonarr", "hunted", len(episode_ids))
                sonarr_logger.debug(f"Incremented sonarr hunted statistics by {len(episode_ids)}")
            else:
                sonarr_logger.warning(f"Episode search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed yet.")
        else:
            sonarr_logger.error(f"Failed to trigger search command for episodes {episode_ids} in series {series_id}.")

    sonarr_logger.info("Finished missing episodes processing cycle for Sonarr.")
    return processed_any

def process_missing_seasons_packs_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
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
    
    # Get all missing episodes in one call instead of per-series
    missing_episodes = sonarr_api.get_missing_episodes(api_url, api_key, api_timeout, monitored_only)
    if not missing_episodes:
        sonarr_logger.info("No missing episodes found")
        return False
    
    # Group episodes by series and season
    missing_seasons = {}
    for episode in missing_episodes:
        if monitored_only and not episode.get('monitored', False):
            continue
            
        series_id = episode.get('seriesId')
        if not series_id:
            continue
            
        season_number = episode.get('seasonNumber')
        series_title = episode.get('series', {}).get('title', 'Unknown Series')
        
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
    
    # Filter out already processed seasons
    unprocessed_seasons = []
    for season in seasons_list:
        season_id = f"{season['series_id']}_{season['season_number']}"
        if not is_processed("sonarr", instance_name, season_id):
            unprocessed_seasons.append(season)
        else:
            sonarr_logger.debug(f"Skipping already processed season ID: {season_id}")
    
    sonarr_logger.info(f"Found {len(unprocessed_seasons)} unprocessed seasons with missing episodes out of {len(seasons_list)} total.")
    
    if not unprocessed_seasons:
        sonarr_logger.info("All seasons with missing episodes have been processed.")
        return False
    
    # Apply randomization if requested
    random.shuffle(unprocessed_seasons)
    
    # Process up to hunt_missing_items seasons
    processed_count = 0
    
    # Add detailed logging for selected seasons
    if unprocessed_seasons and hunt_missing_items > 0:
        seasons_to_process = unprocessed_seasons[:hunt_missing_items]
        sonarr_logger.info(f"Randomly selected {min(len(unprocessed_seasons), hunt_missing_items)} seasons with missing episodes:")
        
        for idx, season in enumerate(seasons_to_process):
            sonarr_logger.info(f"  {idx+1}. {season['series_title']} - Season {season['season_number']} ({season['episode_count']} missing episodes) (Series ID: {season['series_id']})")
    
    for season in unprocessed_seasons:
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
            
            # Add season to processed list
            season_id = f"{series_id}_{season_number}"
            add_processed_id("sonarr", instance_name, season_id)
            sonarr_logger.debug(f"Added season ID {season_id} to processed list for {instance_name}")
            
            # Wait for command to complete if configured
            if command_wait_delay > 0 and command_wait_attempts > 0:
                if wait_for_command(
                    api_url, api_key, api_timeout, command_id, 
                    command_wait_delay, command_wait_attempts, "Season Search", stop_check
                ):
                    # Increment stats by the number of episodes in the season
                    increment_stat("sonarr", "hunted", episode_count)
                    sonarr_logger.debug(f"Incremented sonarr hunted statistics by {episode_count} (full season)")
    
    sonarr_logger.info(f"Processed {processed_count} missing season packs for Sonarr.")
    return processed_any

def process_missing_shows_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_future_episodes: bool,
    skip_series_refresh: bool,
    hunt_missing_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process missing episodes in show mode - gets all missing episodes for entire shows."""
    processed_any = False
    
    # Get series with missing episodes
    sonarr_logger.info("Retrieving series with missing episodes...")
    series_with_missing = sonarr_api.get_series_with_missing_episodes(
        api_url, api_key, api_timeout, monitored_only, random_mode=True)
    
    if not series_with_missing:
        sonarr_logger.info("No series with missing episodes found.")
        return False
    
    # Filter out shows that have been processed
    unprocessed_series = []
    for series in series_with_missing:
        series_id = str(series.get("series_id"))
        if not is_processed("sonarr", instance_name, series_id):
            unprocessed_series.append(series)
        else:
            sonarr_logger.debug(f"Skipping already processed series ID: {series_id}")
    
    sonarr_logger.info(f"Found {len(unprocessed_series)} unprocessed series with missing episodes out of {len(series_with_missing)} total.")
    
    if not unprocessed_series:
        sonarr_logger.info("All series with missing episodes have been processed.")
        return False
        
    # Select the shows to process (random or sequential)
    shows_to_process = random.sample(
        unprocessed_series, 
        min(len(unprocessed_series), hunt_missing_items)
    )
    
    # Add detailed logging for selected shows
    if shows_to_process:
        sonarr_logger.info("Shows selected for processing in this cycle:")
        for idx, show in enumerate(shows_to_process):
            show_id = show.get('series_id')
            show_title = show.get('series_title', 'Unknown Show')
            # Count total missing episodes across all seasons
            episode_count = sum(season.get('episode_count', 0) for season in show.get('seasons', []))
            sonarr_logger.info(f"  {idx+1}. {show_title} ({episode_count} missing episodes) (Show ID: {show_id})")
    
    # Process each show
    for show in shows_to_process:
        if stop_check():
            sonarr_logger.info("Stop requested. Aborting show processing.")
            break
        
        show_id = show.get('series_id')
        show_title = show.get('series_title', 'Unknown Show')
        
        # Get missing episodes for this show
        missing_episodes = []
        for season in show.get('seasons', []):
            missing_episodes.extend(season.get('episodes', []))
        
        # Filter out future episodes if needed
        if skip_future_episodes:
            now_unix = time.time()
            original_count = len(missing_episodes)
            missing_episodes = [
                ep for ep in missing_episodes
                if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
            ]
            skipped_count = original_count - len(missing_episodes)
            if skipped_count > 0:
                sonarr_logger.info(f"Skipped {skipped_count} future episodes for {show_title} based on air date.")
        
        if not missing_episodes:
            sonarr_logger.info(f"No eligible missing episodes found for {show_title} after filtering.")
            continue
        
        # Log episodes to be processed
        sonarr_logger.info(f"Processing {len(missing_episodes)} missing episodes for show: {show_title}")
        for idx, episode in enumerate(missing_episodes[:5]):  # Only log first 5 for brevity
            season = episode.get('seasonNumber', 'Unknown')
            ep_num = episode.get('episodeNumber', 'Unknown')
            title = episode.get('title', 'Unknown Title')
            sonarr_logger.debug(f"  {idx+1}. S{season:02d}E{ep_num:02d} - {title}")
        
        if len(missing_episodes) > 5:
            sonarr_logger.debug(f"  ... and {len(missing_episodes)-5} more episodes.")
        
        # Refresh series if not skipped
        if not skip_series_refresh:
            sonarr_logger.info(f"Refreshing series info for {show_title}...")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, show_id)
            if refresh_command_id:
                wait_success = wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh", stop_check
                )
                if not wait_success:
                    sonarr_logger.warning(f"Series refresh command timed out or failed for {show_title}. Proceeding with search anyway.")
            else:
                sonarr_logger.warning(f"Failed to trigger refresh command for {show_title}. Proceeding with search anyway.")
        
        # Extract episode IDs to search
        episode_ids = [episode.get('id') for episode in missing_episodes if episode.get('id')]
        
        if not episode_ids:
            sonarr_logger.warning(f"No valid episode IDs found for {show_title}.")
            continue
        
        # Search for all episodes in the show
        sonarr_logger.info(f"Searching for {len(episode_ids)} missing episodes for {show_title}...")
        search_successful = sonarr_api.search_episode(api_url, api_key, api_timeout, episode_ids)
        
        if search_successful:
            processed_any = True
            sonarr_logger.info(f"Successfully processed {len(episode_ids)} missing episodes in {show_title}")
            
            # Add series ID to processed list
            add_processed_id("sonarr", instance_name, str(show_id))
            sonarr_logger.debug(f"Added series ID {show_id} to processed list for {instance_name}")
            
            # Add episode IDs to stateful manager
            for episode_id in episode_ids:
                add_processed_id("sonarr", instance_name, str(episode_id))
            
            # Increment the hunted statistics
            increment_stat("sonarr", "hunted", len(episode_ids))
            sonarr_logger.debug(f"Incremented sonarr hunted statistics by {len(episode_ids)}")
        else:
            sonarr_logger.error(f"Failed to trigger search for {show_title}.")
    
    sonarr_logger.info("Show-based missing episode processing complete.")
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