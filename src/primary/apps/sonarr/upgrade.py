#!/usr/bin/env python3
"""
Sonarr cutoff upgrade processing module for Huntarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable # Added Callable
# Correct import path
from src.primary.utils.logger import get_logger
# Correct the import names
from src.primary.state import load_processed_ids, save_processed_ids
from src.primary.apps.sonarr import api as sonarr_api # Import the updated api module
from src.primary.apps.sonarr.missing import wait_for_command # Reuse wait function

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

# State file for processed upgrades
PROCESSED_UPGRADES_FILE = "processed_upgrades_sonarr.json"

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool]
) -> bool:
    """Process cutoff unmet episodes in Sonarr for quality upgrades."""
    sonarr_logger.info("Starting cutoff upgrade processing cycle for Sonarr.")
    processed_any = False

    # Extract necessary settings from app_settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Increased default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_episodes = app_settings.get("skip_future_episodes", True)
    skip_series_refresh = app_settings.get("skip_series_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    hunt_upgrade_episodes = app_settings.get("hunt_upgrade_episodes", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    
    # New setting to determine when to use random page selection (default to 1000 as threshold)
    large_library_threshold = app_settings.get("large_library_threshold", 1000)

    if not api_url or not api_key:
        sonarr_logger.error("API URL or Key not configured in settings. Cannot process upgrades.")
        return False

    if hunt_upgrade_episodes <= 0:
        sonarr_logger.info("'hunt_upgrade_episodes' setting is 0 or less. Skipping upgrade processing.")
        return False
        
    sonarr_logger.info(f"Checking for {hunt_upgrade_episodes} quality upgrades...")

    # Load already processed episode IDs for upgrades
    processed_upgrade_ids: Set[int] = set(load_processed_ids(PROCESSED_UPGRADES_FILE))
    sonarr_logger.debug(f"Loaded {len(processed_upgrade_ids)} processed upgrade episode IDs for Sonarr.")

    # Use different methods based on random setting and library size
    episodes_to_search = []
    
    if random_upgrades:
        # Use the efficient random page selection method
        sonarr_logger.debug(f"Using random selection for cutoff unmet episodes")
        episodes_to_search = sonarr_api.get_cutoff_unmet_episodes_random_page(
            api_url, api_key, api_timeout, monitored_only, hunt_upgrade_episodes)
            
        # Filter out already processed episodes
        episodes_to_search = [ep for ep in episodes_to_search if ep['id'] not in processed_upgrade_ids]
        
        # If we didn't get enough episodes, we might need to try another page
        if len(episodes_to_search) < hunt_upgrade_episodes and len(episodes_to_search) > 0:
            sonarr_logger.debug(f"Got {len(episodes_to_search)} episodes from random page, fewer than requested {hunt_upgrade_episodes}")
    else:
        # Use the sequential approach for non-random selection
        sonarr_logger.debug(f"Using sequential selection for cutoff unmet episodes (oldest first)")
        cutoff_unmet_episodes = sonarr_api.get_cutoff_unmet_episodes(
            api_url, api_key, api_timeout, monitored_only)
            
        if not cutoff_unmet_episodes:
            sonarr_logger.info("No cutoff unmet episodes found in Sonarr.")
            return False
            
        # Filter out already processed episodes
        episodes_to_process = [ep for ep in cutoff_unmet_episodes if ep['id'] not in processed_upgrade_ids]
        sonarr_logger.info(f"Found {len(episodes_to_process)} new cutoff unmet episodes to process for upgrades.")
        
        # Filter out future episodes if configured
        if skip_future_episodes:
            now_unix = time.time()
            original_count = len(episodes_to_process)
            # Ensure airDateUtc exists and is not None before parsing
            episodes_to_process = [
                ep for ep in episodes_to_process
                if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
            ]
            skipped_count = original_count - len(episodes_to_process)
            if skipped_count > 0:
                sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date for upgrades.")
                
        # Select the first N episodes
        episodes_to_search = episodes_to_process[:hunt_upgrade_episodes]

    if stop_check(): 
        sonarr_logger.info("Stop requested during upgrade processing.")
        return processed_any
        
    # Filter out future episodes for random selection approach
    if random_upgrades and skip_future_episodes:
        now_unix = time.time()
        original_count = len(episodes_to_search)
        episodes_to_search = [
            ep for ep in episodes_to_search
            if ep.get('airDateUtc') and time.mktime(time.strptime(ep['airDateUtc'], '%Y-%m-%dT%H:%M:%SZ')) < now_unix
        ]
        skipped_count = original_count - len(episodes_to_search)
        if skipped_count > 0:
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date for upgrades.")

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
    processed_in_this_run = set()
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
                # Mark episodes as processed for upgrades if search command completed successfully
                processed_in_this_run.update(episode_ids)
                processed_any = True # Mark that we did something
                sonarr_logger.info(f"Successfully processed and searched for upgrades for {len(episode_ids)} episodes in series {series_id}.")
            else:
                sonarr_logger.warning(f"Episode upgrade search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed for upgrades yet.")
        else:
            sonarr_logger.error(f"Failed to trigger upgrade search command for episodes {episode_ids} in series {series_id}.")

    # Update the set of processed upgrade episode IDs and save to state file
    if processed_in_this_run:
        updated_processed_ids = processed_upgrade_ids.union(processed_in_this_run)
        save_processed_ids(PROCESSED_UPGRADES_FILE, list(updated_processed_ids))
        sonarr_logger.info(f"Saved {len(processed_in_this_run)} newly processed upgrade episode IDs for Sonarr. Total processed for upgrades: {len(updated_processed_ids)}.")
    elif processed_any:
        sonarr_logger.info("Attempted upgrade processing, but no new episodes were marked as successfully processed.")

    sonarr_logger.info("Finished cutoff upgrade processing cycle for Sonarr.")
    return processed_any