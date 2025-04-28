#!/usr/bin/env python3
"""
Sonarr cutoff upgrade processing module for Huntarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.apps.sonarr import api as sonarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
sonarr_logger = get_logger("sonarr")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Sonarr based on settings.

    Args:
        app_settings: Dictionary containing all settings for Sonarr.
        stop_check: A function that returns True if the process should stop.

    Returns:
        True if any episodes were processed, False otherwise.
    """
    sonarr_logger.info("Starting quality cutoff upgrades processing cycle for Sonarr.")
    processed_any = False

    # Extract necessary settings
    api_url = app_settings.get("api_url", "").strip()
    api_key = app_settings.get("api_key", "").strip()
    api_timeout = app_settings.get("api_timeout", 90)
    monitored_only = app_settings.get("monitored_only", True)
    skip_series_refresh = app_settings.get("skip_series_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    hunt_upgrade_episodes = app_settings.get("hunt_upgrade_episodes", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)

    # Improved validation of API URL and key
    if not api_url:
        sonarr_logger.error("API URL is empty or not set")
        return False
        
    if not api_key:
        sonarr_logger.error("API Key is not set")
        return False
        
    # Ensure URL has proper format with auto-correction
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        old_url = api_url
        api_url = f"http://{api_url}"
        sonarr_logger.warning(f"API URL is missing http:// or https:// scheme: {old_url}")
        sonarr_logger.warning(f"Auto-correcting URL to: {api_url}")
        
    sonarr_logger.debug(f"Using API URL: {api_url}")

    if hunt_upgrade_episodes <= 0:
        sonarr_logger.info("'hunt_upgrade_episodes' setting is 0 or less. Skipping upgrade processing.")
        return False
        
    sonarr_logger.info(f"Checking for {hunt_upgrade_episodes} quality upgrades...")

    # Use different methods based on random setting and library size
    episodes_to_search = []
    
    if random_upgrades:
        # Use the efficient random page selection method
        sonarr_logger.debug(f"Using random selection for cutoff unmet episodes")
        episodes_to_search = sonarr_api.get_cutoff_unmet_episodes_random_page(
            api_url, api_key, api_timeout, monitored_only, hunt_upgrade_episodes)
            
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
                
        # Select the first N episodes
        episodes_to_search = cutoff_unmet_episodes[:hunt_upgrade_episodes]

    if stop_check(): 
        sonarr_logger.info("Stop requested during upgrade processing.")
        return processed_any
        
    # Filter out future episodes for random selection approach
    if random_upgrades and skip_series_refresh:
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
                # Increment the upgraded statistics
                increment_stat("sonarr", "upgraded", len(episode_ids))
                sonarr_logger.debug(f"Incremented sonarr upgraded statistics by {len(episode_ids)}")
                sonarr_logger.info(f"Successfully processed and searched for upgrades for {len(episode_ids)} episodes in series {series_id}.")
                processed_any = True # Mark that we did something
            else:
                sonarr_logger.warning(f"Episode upgrade search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed for upgrades yet.")
        else:
            sonarr_logger.error(f"Failed to trigger upgrade search command for episodes {episode_ids} in series {series_id}.")

    sonarr_logger.info("Finished cutoff upgrade processing cycle for Sonarr.")
    return processed_any

def wait_for_command(
    api_url: str,
    api_key: str,
    api_timeout: int,
    command_id: int,
    delay: int,
    attempts: int,
    command_name: str,
    stop_check: Callable[[], bool] # Pass stop check function
) -> bool:
    """Wait for a Sonarr command to complete, checking for stop requests."""
    # Ensure URL has proper format with auto-correction
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        old_url = api_url
        api_url = f"http://{api_url}"
        sonarr_logger.warning(f"API URL is missing http:// or https:// scheme in wait_for_command: {old_url}")
        sonarr_logger.warning(f"Auto-correcting URL to: {api_url}")
    
    sonarr_logger.debug(f"Waiting for Sonarr command '{command_name}' (ID: {command_id}) to complete...")
    for attempt in range(attempts):
        if stop_check():
            sonarr_logger.info(f"Stop requested while waiting for command '{command_name}' (ID: {command_id}).")
            return False # Indicate command did not complete successfully due to stop

        status_data = sonarr_api.get_command_status(api_url, api_key, api_timeout, command_id)
        if status_data:
            status = status_data.get('status')
            if status == 'completed':
                sonarr_logger.info(f"Sonarr command '{command_name}' (ID: {command_id}) completed successfully.")
                return True
            elif status in ['failed', 'aborted']:
                # Try to get a more specific error message if available
                body = status_data.get('body', {})
                error_message = body.get('message') # Check for 'message' first
                if not error_message:
                    error_message = body.get('exception', f"Command {status}") # Fallback to exception
                sonarr_logger.error(f"Sonarr command '{command_name}' (ID: {command_id}) {status}. Error: {error_message}")
                return False
            else: # queued, started, running
                sonarr_logger.debug(f"Sonarr command '{command_name}' (ID: {command_id}) status: {status}. Waiting {delay}s... (Attempt {attempt + 1}/{attempts})")
        else:
            sonarr_logger.warning(f"Could not get status for Sonarr command '{command_name}' (ID: {command_id}). Retrying... (Attempt {attempt + 1}/{attempts})")

        # Wait for the delay, but check stop_check frequently (e.g., every second)
        wait_start_time = time.monotonic()
        while time.monotonic() < wait_start_time + delay:
            if stop_check():
                sonarr_logger.info(f"Stop requested while waiting between checks for command '{command_name}' (ID: {command_id}).")
                return False
            time.sleep(min(1, delay - (time.monotonic() - wait_start_time))) # Sleep 1s or remaining time

    sonarr_logger.error(f"Sonarr command '{command_name}' (ID: {command_id}) timed out after {attempts} attempts.")
    return False