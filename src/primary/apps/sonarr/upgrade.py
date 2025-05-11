#!/usr/bin/env python3
"""
Sonarr cutoff upgrade processing module for Huntarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable, Union
from src.primary.utils.logger import get_logger
from src.primary.apps.sonarr import api as sonarr_api
from src.primary.stats_manager import increment_stat
from src.primary.stateful_manager import is_processed, add_processed_id
from src.primary.utils.history_utils import log_processed_media
from src.primary.settings_manager import get_advanced_setting

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

def process_cutoff_upgrades(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int = get_advanced_setting("api_timeout", 120),
    monitored_only: bool = True,
    skip_series_refresh: bool = False,
    hunt_upgrade_items: int = 5,
    upgrade_mode: str = "episodes",
    command_wait_delay: int = get_advanced_setting("command_wait_delay", 1),
    command_wait_attempts: int = get_advanced_setting("command_wait_attempts", 600),
    stop_check: Callable[[], bool] = lambda: False
) -> bool:
    """
    Process quality cutoff upgrades for Sonarr.
    This can use either episodes mode or shows mode for upgrades based on the upgrade_mode setting.
    """
    if hunt_upgrade_items <= 0:
        sonarr_logger.info("'hunt_upgrade_items' setting is 0 or less. Skipping upgrade processing.")
        return False
        
    sonarr_logger.info(f"Checking for {hunt_upgrade_items} quality upgrades...")
    
    sonarr_logger.info(f"Using {upgrade_mode.upper()} mode for quality upgrades")

    # Use the selected upgrade_mode
    if upgrade_mode == "shows":
        return process_upgrade_shows_mode(
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_series_refresh, hunt_upgrade_items, 
            command_wait_delay, command_wait_attempts, stop_check
        )
    elif upgrade_mode == "seasons_packs":
        return process_upgrade_seasons_mode(
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_series_refresh, hunt_upgrade_items, 
            command_wait_delay, command_wait_attempts, stop_check
        )
    else:  # Default to episodes mode
        return process_upgrade_episodes_mode(
            api_url, api_key, instance_name, api_timeout, monitored_only, 
            skip_series_refresh, hunt_upgrade_items, 
            command_wait_delay, command_wait_attempts, stop_check
        )

def process_upgrade_episodes_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
    hunt_upgrade_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process upgrades in episode mode (original implementation)."""
    processed_any = False
    
    # Always use the efficient random page selection method
    sonarr_logger.debug(f"Using random selection for cutoff unmet episodes")
    episodes_to_search = sonarr_api.get_cutoff_unmet_episodes_random_page(
        api_url, api_key, api_timeout, monitored_only, hunt_upgrade_items)
        
    # If we didn't get enough episodes, we might need to try another page
    if len(episodes_to_search) < hunt_upgrade_items and len(episodes_to_search) > 0:
        sonarr_logger.debug(f"Got {len(episodes_to_search)} episodes from random page, fewer than requested {hunt_upgrade_items}")
    
    if stop_check(): 
        sonarr_logger.info("Stop requested during upgrade processing.")
        return processed_any
        
    # Filter out future episodes for random selection approach
    if skip_series_refresh:
        now_unix = time.time()
        original_count = len(episodes_to_search)
        episodes_to_search = [
            ep for ep in episodes_to_search
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(episodes_to_search)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date for upgrades.")
    
    # Filter out already processed episodes for random selection approach
    unprocessed_episodes = []
    for episode in episodes_to_search:
        episode_id = str(episode.get("id"))
        if not is_processed("sonarr", instance_name, episode_id):
            unprocessed_episodes.append(episode)
        else:
            sonarr_logger.debug(f"Skipping already processed episode ID for upgrade: {episode_id}")
        
    sonarr_logger.info(f"Found {len(unprocessed_episodes)} unprocessed cutoff unmet episodes out of {len(episodes_to_search)} total.")
    episodes_to_search = unprocessed_episodes

    if not episodes_to_search:
        sonarr_logger.info("No cutoff unmet episodes left to process for upgrades after filtering.")
        return False

    sonarr_logger.info(f"Selected {len(episodes_to_search)} cutoff unmet episodes to search for upgrades.")
    
    # Add detailed listing of episodes being upgraded
    if episodes_to_search:
        sonarr_logger.info(f"Episodes selected for quality upgrades in this cycle:")
        for idx, episode in enumerate(episodes_to_search):
            series_title = episode.get('series', {}).get('title', 'Unknown Series')
            episode_title = episode.get('title', 'Unknown Episode')
            season_number = episode.get('seasonNumber', 'Unknown Season')
            episode_number = episode.get('episodeNumber', 'Unknown Episode')
            
            # Get quality information
            quality_name = "Unknown"
            if "quality" in episode and episode["quality"]:
                quality_name = episode["quality"].get("quality", {}).get("name", "Unknown")
                
            episode_id = episode.get("id")
            try:
                season_episode = f"S{season_number:02d}E{episode_number:02d}"
            except (ValueError, TypeError):
                season_episode = f"S{season_number}E{episode_number}"
                
            sonarr_logger.info(f" {idx+1}. {series_title} - {season_episode} - \"{episode_title}\" - Current quality: {quality_name} (ID: {episode_id})")
    
    # Group episodes by series for potential refresh
    series_to_process: Dict[int, List[int]] = {}
    series_titles: Dict[int, str] = {} # Store titles for logging
    for episode in episodes_to_search:
        series_id = episode.get('seriesId')
        if series_id:
            if series_id not in series_to_process:
                series_to_process[series_id] = []
                # Store title when first encountering the series ID
                series_titles[series_id] = episode.get('series', {}).get('title', f"Series ID {series_id}")
            series_to_process[series_id].append(episode['id'])

    # Process each series
    for series_id, episode_ids in series_to_process.items():
        if stop_check(): 
            sonarr_logger.info("Stop requested before processing next series for upgrades.")
            break
            
        series_title = series_titles.get(series_id, f"Series ID {series_id}")
        sonarr_logger.info(f"Processing series for upgrades: {series_title} (ID: {series_id}) with {len(episode_ids)} episodes.")

        # Refresh series metadata if not skipped
        refresh_command_id = None
        if not skip_series_refresh:
            sonarr_logger.debug(f"Attempting to refresh series ID: {series_id} before upgrade search.")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                # Wait for refresh command to complete
                if not wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh (Upgrade)", stop_check
                ):
                    sonarr_logger.warning(f"Series refresh command (ID: {refresh_command_id}) for series {series_id} did not complete successfully or timed out. Proceeding with upgrade search anyway.")
            else:
                 sonarr_logger.warning(f"Failed to trigger refresh command for series ID: {series_id}. Proceeding without refresh.")
        else:
            sonarr_logger.debug(f"Skipping series refresh for series ID: {series_id} as configured.")

        if stop_check(): 
            sonarr_logger.info("Stop requested after series refresh attempt for upgrades.")
            break

        # Trigger search for the selected episodes in this series
        sonarr_logger.debug(f"Attempting upgrade search for episode IDs: {episode_ids}")
        search_command_id = sonarr_api.search_episode(api_url, api_key, api_timeout, episode_ids)

        if search_command_id:
            # Wait for search command to complete
            if wait_for_command(
                api_url, api_key, api_timeout, search_command_id,
                command_wait_delay, command_wait_attempts, "Episode Upgrade Search", stop_check
            ):
                # Mark episodes as processed if search command completed successfully
                processed_any = True # Mark that we did something
                sonarr_logger.info(f"Successfully processed and searched for {len(episode_ids)} episodes in series {series_id}.")
                
                # Add stats incrementing right here - this is the code path that's actually being executed
                for episode_id in episode_ids:
                    # Increment stat for each episode individually, just like Radarr
                    increment_stat("sonarr", "upgraded")
                    sonarr_logger.info(f"*** STATS INCREMENT *** sonarr upgraded by 1 for episode ID {episode_id}")
                
                # Mark episodes as processed using stateful management
                for episode_id in episode_ids:
                    add_processed_id("sonarr", instance_name, str(episode_id))
                    sonarr_logger.debug(f"Marked episode ID {episode_id} as processed for upgrades")
                    
                    # Find the episode information for history logging
                    # We need to get the episode details from the API to include proper info in history
                    try:
                        episode_details = sonarr_api.get_episode(api_url, api_key, api_timeout, episode_id)
                        if episode_details:
                            series_title = episode_details.get('series', {}).get('title', 'Unknown Series')
                            episode_title = episode_details.get('title', 'Unknown Episode')
                            season_number = episode_details.get('seasonNumber', 'Unknown Season')
                            episode_number = episode_details.get('episodeNumber', 'Unknown Episode')
                            
                            try:
                                season_episode = f"S{season_number:02d}E{episode_number:02d}"
                            except (ValueError, TypeError):
                                season_episode = f"S{season_number}E{episode_number}"
                                
                            # Record the upgrade in history with quality upgrade identifier
                            media_name = f"{series_title} - {season_episode} - {episode_title}"
                            log_processed_media("sonarr", media_name, episode_id, instance_name, "upgrade")
                            sonarr_logger.debug(f"Logged quality upgrade to history for episode ID {episode_id}")
                    except Exception as e:
                        sonarr_logger.error(f"Failed to log history for episode ID {episode_id}: {str(e)}")
            else:
                sonarr_logger.warning(f"Episode upgrade search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed yet.")
        else:
            sonarr_logger.error(f"Failed to trigger upgrade search command for episodes {episode_ids} in series {series_id}.")

    sonarr_logger.info("Finished quality cutoff upgrades processing cycle for Sonarr.")
    return processed_any

def log_season_pack_upgrade(api_url: str, api_key: str, api_timeout: int, series_id: int, season_number: int, instance_name: str):
    """Log a season pack upgrade to the history."""
    try:
        # Get series details for better history logging
        series_details = sonarr_api.get_series(api_url, api_key, api_timeout, series_id)
        if series_details:
            series_title = series_details.get('title', f"Series ID {series_id}")
            
            # Format season number for display
            try:
                season_id = f"S{season_number:02d}" if isinstance(season_number, int) else f"S{season_number}"
            except (ValueError, TypeError):
                season_id = f"S{season_number}"
            
            # Use the season ID directly - format as series_id + season number
            # This matches how Sonarr would identify a season
            season_id_num = f"{series_id}_{season_number}"
            
            # Create a descriptive name for the history entry
            media_name = f"{series_title} - {season_id} - COMPLETE SEASON PACK"
            
            # Log the season pack upgrade to history with normal 'upgrade' operation type
            log_processed_media("sonarr", media_name, season_id_num, instance_name, "upgrade")
            sonarr_logger.debug(f"Logged season pack upgrade to history for {series_title} Season {season_number}")
    except Exception as e:
        sonarr_logger.error(f"Failed to log season pack upgrade to history: {str(e)}")

def process_upgrade_seasons_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
    hunt_upgrade_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process upgrades in season mode - groups episodes by season."""
    processed_any = False
    
    # Use the efficient random page selection method to get a sample of cutoff unmet episodes
    sonarr_logger.debug(f"Using random page selection for cutoff unmet episodes")
    # Request slightly more episodes than needed to ensure we have enough for a few seasons
    sample_size = hunt_upgrade_items * 10
    cutoff_unmet_episodes = sonarr_api.get_cutoff_unmet_episodes_random_page(
        api_url, api_key, api_timeout, monitored_only, sample_size)
    
    sonarr_logger.info(f"Received {len(cutoff_unmet_episodes)} cutoff unmet episodes from random page (before filtering).")
    
    if not cutoff_unmet_episodes:
        sonarr_logger.info("No cutoff unmet episodes found in Sonarr.")
        return False
        
    # Filter out future episodes if configured
    if skip_series_refresh:
        now_unix = time.time()
        original_count = len(cutoff_unmet_episodes)
        # Ensure airDateUtc exists and is not None before parsing
        cutoff_unmet_episodes = [
            ep for ep in cutoff_unmet_episodes
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(cutoff_unmet_episodes)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date for upgrades.")
    
    if stop_check(): 
        sonarr_logger.info("Stop requested during upgrade processing.")
        return processed_any
    
    # Group episodes by series and season
    series_season_episodes: Dict[int, Dict[int, List[Dict]]] = {}
    for episode in cutoff_unmet_episodes:
        series_id = episode.get('seriesId')
        season_number = episode.get('seasonNumber')
        
        if series_id is not None and season_number is not None:
            if series_id not in series_season_episodes:
                series_season_episodes[series_id] = {}
            
            if season_number not in series_season_episodes[series_id]:
                series_season_episodes[series_id][season_number] = []
                
            series_season_episodes[series_id][season_number].append(episode)
    
    # Create a list of (series_id, season_number) tuples for selection
    available_seasons = []
    for series_id, seasons in series_season_episodes.items():
        for season_number, episodes in seasons.items():
            # Get series title from the first episode for this season
            series_title = episodes[0].get('series', {}).get('title', f"Series ID {series_id}")
            available_seasons.append((series_id, season_number, len(episodes), series_title))
    
    if not available_seasons:
        sonarr_logger.info("No valid seasons with cutoff unmet episodes found.")
        return False
    
    # Select seasons to process - always randomly
    random.shuffle(available_seasons)
    seasons_to_process = available_seasons[:hunt_upgrade_items]
    
    sonarr_logger.info(f"Selected {len(seasons_to_process)} seasons with cutoff unmet episodes to process")
    
    # Log selected seasons
    for idx, (series_id, season_number, episode_count, series_title) in enumerate(seasons_to_process):
        sonarr_logger.info(f" {idx+1}. {series_title} - Season {season_number} - {episode_count} cutoff unmet episodes")
    
    # Process each selected season
    for series_id, season_number, _, series_title in seasons_to_process:
        if stop_check(): 
            sonarr_logger.info("Stop requested before processing next season.")
            break
            
        episodes = series_season_episodes[series_id][season_number]
        episode_ids = [episode["id"] for episode in episodes]
        
        sonarr_logger.info(f"Processing {series_title} - Season {season_number} with {len(episode_ids)} cutoff unmet episodes")
        
        # Refresh series metadata if not skipped
        if not skip_series_refresh:
            sonarr_logger.debug(f"Attempting to refresh series ID: {series_id}")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                # Wait for refresh command to complete
                if not wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh (Upgrade)", stop_check
                ):
                    sonarr_logger.warning(f"Series refresh command for {series_title} did not complete successfully or timed out.")
            else:
                sonarr_logger.warning(f"Failed to trigger refresh command for series {series_title}")
                
        if stop_check(): 
            sonarr_logger.info("Stop requested after series refresh attempt.")
            break
            
        # Trigger search for the entire season instead of individual episodes
        sonarr_logger.debug(f"Attempting to search for entire Season {season_number} of {series_title} for upgrades")
        search_command_id = sonarr_api.search_season(api_url, api_key, api_timeout, series_id, season_number)
        
        if search_command_id:
            # Wait for search command to complete
            if wait_for_command(
                api_url, api_key, api_timeout, search_command_id,
                command_wait_delay, command_wait_attempts, "Episode Upgrade Search", stop_check
            ):
                # Mark as processed if search command completed successfully
                processed_any = True
                sonarr_logger.info(f"Successfully triggered season pack search for {series_title} Season {season_number} with {len(episode_ids)} cutoff unmet episodes")
                
                # Log this as a season pack upgrade in the history
                log_season_pack_upgrade(api_url, api_key, api_timeout, series_id, season_number, instance_name)
                
                # We'll increment stats individually for each episode instead of in batch
                # increment_stat("sonarr", "upgraded", len(episode_ids))
                # sonarr_logger.debug(f"Incremented sonarr upgraded statistics by {len(episode_ids)}")
                
                # Mark episodes as processed using stateful management
                for episode_id in episode_ids:
                    add_processed_id("sonarr", instance_name, str(episode_id))
                    sonarr_logger.debug(f"Marked episode ID {episode_id} as processed for upgrades")
                    
                    # Increment stats for this episode (consistent with Radarr's approach)
                    increment_stat("sonarr", "upgraded")
                    sonarr_logger.debug(f"Incremented sonarr upgraded statistic for episode {episode_id}")
                    
                    # Find the episode information for history logging
                    # We need to get the episode details from the API to include proper info in history
                    try:
                        episode_details = sonarr_api.get_episode(api_url, api_key, api_timeout, episode_id)
                        if episode_details:
                            series_title = episode_details.get('series', {}).get('title', 'Unknown Series')
                            episode_title = episode_details.get('title', 'Unknown Episode')
                            season_number = episode_details.get('seasonNumber', 'Unknown Season')
                            episode_number = episode_details.get('episodeNumber', 'Unknown Episode')
                            
                            try:
                                season_episode = f"S{season_number:02d}E{episode_number:02d}"
                            except (ValueError, TypeError):
                                season_episode = f"S{season_number}E{episode_number}"
                                
                            # Record the upgrade in history with quality upgrade identifier
                            media_name = f"{series_title} - {season_episode} - {episode_title}"
                            log_processed_media("sonarr", media_name, episode_id, instance_name, "upgrade")
                            sonarr_logger.debug(f"Logged quality upgrade to history for episode ID {episode_id}")
                    except Exception as e:
                        sonarr_logger.error(f"Failed to log history for episode ID {episode_id}: {str(e)}")
            else:
                sonarr_logger.warning(f"Season pack search command for {series_title} Season {season_number} did not complete successfully")
        else:
            sonarr_logger.error(f"Failed to trigger season pack search command for {series_title} Season {season_number}")
    
    sonarr_logger.info("Finished quality cutoff upgrades processing cycle (season mode) for Sonarr.")
    return processed_any

def process_upgrade_shows_mode(
    api_url: str,
    api_key: str,
    instance_name: str,
    api_timeout: int,
    monitored_only: bool,
    skip_series_refresh: bool,
    hunt_upgrade_items: int,
    command_wait_delay: int,
    command_wait_attempts: int,
    stop_check: Callable[[], bool]
) -> bool:
    """Process upgrades in show mode - gets all cutoff unmet episodes for entire shows."""
    processed_any = False
    
    # Use the efficient random page selection method to get a sample of cutoff unmet episodes
    sonarr_logger.debug(f"Using random page selection for cutoff unmet episodes in shows mode")
    # Request slightly more episodes than needed to ensure we have enough for a few shows
    sample_size = hunt_upgrade_items * 20  # Use a larger multiplier for shows mode
    cutoff_unmet_sample = sonarr_api.get_cutoff_unmet_episodes_random_page(
        api_url, api_key, api_timeout, monitored_only, sample_size)
    
    sonarr_logger.info(f"Received {len(cutoff_unmet_sample)} cutoff unmet episodes from random page (before filtering).")
    
    if not cutoff_unmet_sample:
        sonarr_logger.info("No cutoff unmet episodes found in Sonarr.")
        return False
        
    # Filter out future episodes if configured
    if skip_series_refresh:
        now_unix = time.time()
        original_count = len(cutoff_unmet_sample)
        # Ensure airDateUtc exists and is not None before parsing
        cutoff_unmet_sample = [
            ep for ep in cutoff_unmet_sample
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(cutoff_unmet_sample)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date for upgrades.")
    
    if stop_check(): 
        sonarr_logger.info("Stop requested during upgrade processing.")
        return processed_any
    
    # Group episodes by series to identify candidate shows
    series_info: Dict[int, Dict] = {}  # Store series ID -> {title, sample_count}
    
    for episode in cutoff_unmet_sample:
        series_id = episode.get('seriesId')
        if series_id is not None:
            if series_id not in series_info:
                series_info[series_id] = {
                    'title': episode.get('series', {}).get('title', f"Series ID {series_id}"),
                    'sample_count': 0
                }
            series_info[series_id]['sample_count'] += 1

    # Get list of candidate series from the sample
    series_candidates = []
    for series_id, info in series_info.items():
        series_candidates.append((series_id, info['sample_count'], info['title']))
    
    if not series_candidates:
        sonarr_logger.info("No valid series with cutoff unmet episodes found in sample.")
        return False
        
    # Randomly select up to hunt_upgrade_items series to process
    random.shuffle(series_candidates)
    series_to_process = series_candidates[:hunt_upgrade_items]
    
    sonarr_logger.info(f"Selected {len(series_to_process)} series with cutoff unmet episodes to process")
    
    # Log selected series from sample
    for idx, (series_id, sample_count, series_title) in enumerate(series_to_process):
        sonarr_logger.info(f" {idx+1}. {series_title} - {sample_count} cutoff unmet episodes found in sample")
    
    # Process each selected series
    for series_id, _, series_title in series_to_process:
        if stop_check(): 
            sonarr_logger.info("Stop requested before processing next series.")
            break
            
        # Get ALL cutoff unmet episodes for this series (not just the ones in the sample)
        all_series_episodes = sonarr_api.get_cutoff_unmet_episodes_for_series(
            api_url, api_key, api_timeout, series_id, monitored_only)
        
        # Filter future episodes if needed
        if skip_series_refresh:
            now_unix = time.time()
            original_count = len(all_series_episodes)
            all_series_episodes = [
                ep for ep in all_series_episodes
                if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
            ]
            filtered_count = original_count - len(all_series_episodes)
            if filtered_count > 0:
                sonarr_logger.info(f"Filtered {filtered_count} future episodes from {series_title}")
        
        episode_ids = [episode["id"] for episode in all_series_episodes]
        
        if not episode_ids:
            sonarr_logger.warning(f"No valid episodes found for {series_title} after filtering")
            continue
            
        sonarr_logger.info(f"Processing {series_title} with {len(episode_ids)} cutoff unmet episodes")
        
        # Refresh series metadata if not skipped
        if not skip_series_refresh:
            sonarr_logger.debug(f"Attempting to refresh series ID: {series_id}")
            refresh_command_id = sonarr_api.refresh_series(api_url, api_key, api_timeout, series_id)
            if refresh_command_id:
                # Wait for refresh command to complete
                if not wait_for_command(
                    api_url, api_key, api_timeout, refresh_command_id,
                    command_wait_delay, command_wait_attempts, "Series Refresh (Upgrade)", stop_check
                ):
                    sonarr_logger.warning(f"Series refresh command for {series_title} did not complete successfully or timed out.")
            else:
                sonarr_logger.warning(f"Failed to trigger refresh command for series {series_title}")
                
        if stop_check(): 
            sonarr_logger.info("Stop requested after series refresh attempt.")
            break
            
        # Trigger search for all cutoff unmet episodes in this series
        sonarr_logger.debug(f"Attempting to search for {len(episode_ids)} episodes in {series_title} for upgrades")
        search_command_id = sonarr_api.search_episode(api_url, api_key, api_timeout, episode_ids)
        
        if search_command_id:
            # Wait for search command to complete
            if wait_for_command(
                api_url, api_key, api_timeout, search_command_id,
                command_wait_delay, command_wait_attempts, "Episode Upgrade Search", stop_check
            ):
                # Mark as processed if search command completed successfully
                processed_any = True
                sonarr_logger.info(f"Successfully processed {len(episode_ids)} cutoff unmet episodes in {series_title}")
                
                # We'll increment stats individually for each episode instead of in batch
                # increment_stat("sonarr", "upgraded", len(episode_ids))
                # sonarr_logger.debug(f"Incremented sonarr upgraded statistics by {len(episode_ids)}")
                
                # Mark episodes as processed using stateful management
                for episode_id in episode_ids:
                    add_processed_id("sonarr", instance_name, str(episode_id))
                    sonarr_logger.debug(f"Marked episode ID {episode_id} as processed for upgrades")
                    
                    # Increment stats for this episode (consistent with Radarr's approach)
                    increment_stat("sonarr", "upgraded")
                    sonarr_logger.debug(f"Incremented sonarr upgraded statistic for episode {episode_id}")
                    
                    # Find the episode information for history logging
                    # We need to get the episode details from the API to include proper info in history
                    try:
                        episode_details = sonarr_api.get_episode(api_url, api_key, api_timeout, episode_id)
                        if episode_details:
                            series_title = episode_details.get('series', {}).get('title', 'Unknown Series')
                            episode_title = episode_details.get('title', 'Unknown Episode')
                            season_number = episode_details.get('seasonNumber', 'Unknown Season')
                            episode_number = episode_details.get('episodeNumber', 'Unknown Episode')
                            
                            try:
                                season_episode = f"S{season_number:02d}E{episode_number:02d}"
                            except (ValueError, TypeError):
                                season_episode = f"S{season_number}E{episode_number}"
                                
                            # Record the upgrade in history with quality upgrade identifier
                            media_name = f"{series_title} - {season_episode} - {episode_title}"
                            log_processed_media("sonarr", media_name, episode_id, instance_name, "upgrade")
                            sonarr_logger.debug(f"Logged quality upgrade to history for episode ID {episode_id}")
                    except Exception as e:
                        sonarr_logger.error(f"Failed to log history for episode ID {episode_id}: {str(e)}")
            else:
                sonarr_logger.warning(f"Episode upgrade search command for {series_title} did not complete successfully")
        else:
            sonarr_logger.error(f"Failed to trigger upgrade search command for {series_title}")
    
    sonarr_logger.info("Finished quality cutoff upgrades processing cycle (show mode) for Sonarr.")
    return processed_any

def wait_for_command(
    api_url: str,
    api_key: str,
    api_timeout: int,
    command_id: Union[int, str],
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
    attempts = 0
    while attempts < max_attempts:
        if stop_check():
            sonarr_logger.info(f"Stopping wait for {command_name} due to stop request")
            return False
            
        command_status = sonarr_api.get_command_status(api_url, api_key, api_timeout, command_id)
        if not command_status:
            sonarr_logger.warning(f"Failed to get status for {command_name} (ID: {command_id}), attempt {attempts+1}")
            attempts += 1
            time.sleep(wait_delay)
            continue
            
        status = command_status.get('status')
        if status == 'completed':
            sonarr_logger.debug(f"Sonarr {command_name} (ID: {command_id}) completed successfully")
            return True
        elif status in ['failed', 'aborted']:
            sonarr_logger.warning(f"Sonarr {command_name} (ID: {command_id}) {status}")
            return False
        
        sonarr_logger.debug(f"Sonarr {command_name} (ID: {command_id}) status: {status}, attempt {attempts+1}/{max_attempts}")
        
        attempts += 1
        time.sleep(wait_delay)
    
    sonarr_logger.error(f"Sonarr command '{command_name}' (ID: {command_id}) timed out after {max_attempts} attempts.")
    return False