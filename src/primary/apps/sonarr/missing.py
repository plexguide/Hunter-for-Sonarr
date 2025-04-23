#!/usr/bin/env python3
"""
Sonarr missing episodes processing module for Huntarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
# Correct import path
from src.primary.utils.logger import get_logger
# Correct the import names
from src.primary.state import load_processed_ids, save_processed_ids
from src.primary.apps.sonarr import api as sonarr_api # Import the updated api module

# Get logger for the Sonarr app
sonarr_logger = get_logger("sonarr")

# State file for processed missing episodes
PROCESSED_MISSING_FILE = "processed_missing_sonarr.json"

def process_missing_episodes(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing episodes in Sonarr based on provided settings.

    Args:
        app_settings: Dictionary containing all settings for Sonarr.
        stop_check: A function that returns True if the process should stop.

    Returns:
        True if any episodes were processed, False otherwise.
    """
    sonarr_logger.info("Starting missing episodes processing cycle for Sonarr.")
    processed_any = False

    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 10)
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_episodes = app_settings.get("skip_future_episodes", True)
    skip_series_refresh = app_settings.get("skip_series_refresh", False)
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_shows = app_settings.get("hunt_missing_shows", 0) # Renamed from hunt_missing_episodes for consistency? Check setting name.
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)

    if not api_url or not api_key:
        sonarr_logger.error("API URL or Key not configured in settings. Cannot process missing episodes.")
        return False

    if hunt_missing_shows <= 0:
        sonarr_logger.info("'hunt_missing_shows' setting is 0 or less. Skipping missing episode processing.")
        return False

    # Load already processed episode IDs for Sonarr
    # Use the correct function name
    processed_episode_ids: Set[int] = set(load_processed_ids(PROCESSED_MISSING_FILE))
    sonarr_logger.debug(f"Loaded {len(processed_episode_ids)} processed missing episode IDs for Sonarr.")

    # Get missing episodes from Sonarr API
    missing_episodes = sonarr_api.get_missing_episodes(api_url, api_key, api_timeout, monitored_only)
    if not missing_episodes:
        sonarr_logger.info("No missing episodes found in Sonarr.")
        return False

    if stop_check(): sonarr_logger.info("Stop requested during missing episode processing."); return processed_any

    # Filter out already processed episodes
    episodes_to_process = [ep for ep in missing_episodes if ep['id'] not in processed_episode_ids]
    sonarr_logger.info(f"Found {len(episodes_to_process)} new missing episodes to process.")

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
            sonarr_logger.info(f"Skipped {skipped_count} future episodes based on air date.")

    if not episodes_to_process:
        sonarr_logger.info("No missing episodes left to process after filtering.")
        return False

    # Select episodes to search based on configuration
    if random_missing:
        sonarr_logger.debug(f"Randomly selecting up to {hunt_missing_shows} missing episodes.")
        episodes_to_search = random.sample(episodes_to_process, min(len(episodes_to_process), hunt_missing_shows))
    else:
        sonarr_logger.debug(f"Selecting the first {hunt_missing_shows} missing episodes (oldest first).")
        episodes_to_search = episodes_to_process[:hunt_missing_shows]

    sonarr_logger.info(f"Selected {len(episodes_to_search)} missing episodes to search.")

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
    processed_in_this_run = set()
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
                processed_in_this_run.update(episode_ids)
                processed_any = True # Mark that we did something
                sonarr_logger.info(f"Successfully processed and searched for {len(episode_ids)} episodes in series {series_id}.")
            else:
                sonarr_logger.warning(f"Episode search command (ID: {search_command_id}) for series {series_id} did not complete successfully or timed out. Episodes will not be marked as processed yet.")
        else:
            sonarr_logger.error(f"Failed to trigger search command for episodes {episode_ids} in series {series_id}.")

    # Update the set of processed episode IDs and save to state file
    if processed_in_this_run:
        updated_processed_ids = processed_episode_ids.union(processed_in_this_run)
        # Use the correct function name
        save_processed_ids(PROCESSED_MISSING_FILE, list(updated_processed_ids))
        sonarr_logger.info(f"Saved {len(processed_in_this_run)} newly processed missing episode IDs for Sonarr. Total processed: {len(updated_processed_ids)}.")
    elif processed_any: # Check if we attempted processing but didn't succeed in saving any new IDs
        sonarr_logger.info("Attempted missing episode processing, but no new episodes were marked as successfully processed.")
    # else: # No episodes selected or processed
        # sonarr_logger.info("No new missing episodes were processed in this run.") # Already logged if nothing to process

    sonarr_logger.info("Finished missing episodes processing cycle for Sonarr.")
    return processed_any # Return whether any action was taken

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