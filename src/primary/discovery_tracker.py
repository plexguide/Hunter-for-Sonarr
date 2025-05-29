#!/usr/bin/env python3
"""
Discovery Tracker - Module for tracking if missing items were discovered by Sonarr
Runs independently to check if previously missing episodes are now in Sonarr's wanted list
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.primary.utils.config_paths import get_path
from src.primary.utils.logger import get_logger
from src.primary.history_manager import HISTORY_BASE_PATH, ensure_history_dir
from src.primary import settings_manager
from src.primary.apps.sonarr.api import arr_request

# Create logger for discovery tracking
logger = get_logger("hunting")

# Thread lock for discovery operations
_discovery_lock = threading.Lock()
_discovery_thread = None
_discovery_stop_event = threading.Event()

# Default configuration
DEFAULT_HUNTING_CONFIG = {
    "discovery_check_interval_minutes": 10,
    "discovery_check_days_back": 7,
    "enabled": True
}

def get_hunting_config() -> Dict[str, Any]:
    """Get hunting configuration from hunting.json"""
    try:
        hunting_config_path = get_path('settings', 'hunting.json')
        
        # Create default config if it doesn't exist
        if not hunting_config_path.exists():
            hunting_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(hunting_config_path, 'w') as f:
                json.dump(DEFAULT_HUNTING_CONFIG, f, indent=2)
            logger.info(f"Created default hunting configuration at {hunting_config_path}")
            return DEFAULT_HUNTING_CONFIG.copy()
        
        # Load existing config
        with open(hunting_config_path, 'r') as f:
            config = json.load(f)
        
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_HUNTING_CONFIG.items():
            if key not in config:
                config[key] = value
        
        return config
        
    except Exception as e:
        logger.error(f"Error loading hunting config: {e}")
        return DEFAULT_HUNTING_CONFIG.copy()

def get_sonarr_instances() -> List[Dict[str, Any]]:
    """Get all configured Sonarr instances"""
    try:
        sonarr_settings = settings_manager.load_settings("sonarr")
        if not sonarr_settings or 'instances' not in sonarr_settings:
            return []
        return sonarr_settings['instances']
    except Exception as e:
        logger.error(f"Error getting Sonarr instances: {e}")
        return []

def get_sonarr_wanted_episodes(instance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get wanted episodes from a Sonarr instance"""
    if not instance.get("enabled", True):
        return []
    
    api_url = instance.get("api_url")
    api_key = instance.get("api_key")
    
    if not api_url or not api_key:
        logger.warning(f"Missing API URL or key for Sonarr instance: {instance.get('name', 'Unknown')}")
        return []
    
    try:
        # Get wanted episodes from Sonarr's wanted endpoint
        # Include pageSize in the endpoint URL
        endpoint = "wanted/missing?pageSize=10000"
        response = arr_request(
            api_url=api_url,
            api_key=api_key,
            api_timeout=60,  # Default timeout
            endpoint=endpoint,
            method="GET"
        )
        
        if response and "records" in response:
            logger.info(f"Retrieved {len(response['records'])} wanted episodes from Sonarr instance: {instance.get('name', 'Unknown')}")
            return response["records"]
        else:
            logger.warning(f"No wanted episodes found for Sonarr instance: {instance.get('name', 'Unknown')}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting wanted episodes from Sonarr instance {instance.get('name', 'Unknown')}: {e}")
        return []

def check_episode_in_wanted(episode_info: Dict[str, Any], wanted_episodes: List[Dict[str, Any]]) -> bool:
    """Check if an episode is in the wanted list based on series and episode info"""
    try:
        # Extract episode information from history entry
        episode_title = episode_info.get("episode_title", "")
        series_title = episode_info.get("series_title", "")
        
        # Try to extract season and episode numbers from the title
        # Common formats: S01E01, 1x01, Season 1 Episode 1, etc.
        import re
        
        # Extract season/episode from episode title or entry
        season_episode_patterns = [
            r"S(\d+)E(\d+)",  # S01E01
            r"(\d+)x(\d+)",   # 1x01
            r"Season\s+(\d+)\s+Episode\s+(\d+)",  # Season 1 Episode 1
        ]
        
        season_num = None
        episode_num = None
        
        # Try to extract from episode title first
        for pattern in season_episode_patterns:
            match = re.search(pattern, episode_title, re.IGNORECASE)
            if match:
                season_num = int(match.group(1))
                episode_num = int(match.group(2))
                break
        
        # If not found in episode title, try the series title
        if season_num is None or episode_num is None:
            for pattern in season_episode_patterns:
                match = re.search(pattern, series_title, re.IGNORECASE)
                if match:
                    season_num = int(match.group(1))
                    episode_num = int(match.group(2))
                    break
        
        if season_num is None or episode_num is None:
            logger.debug(f"Could not extract season/episode numbers from: {episode_title} or {series_title}")
            return False
        
        # Look for matching episode in wanted list
        for wanted_ep in wanted_episodes:
            wanted_series = wanted_ep.get("series", {}).get("title", "")
            wanted_season = wanted_ep.get("seasonNumber")
            wanted_episode = wanted_ep.get("episodeNumber")
            
            # Check if series title matches (case insensitive)
            if (wanted_series.lower() in series_title.lower() or 
                series_title.lower() in wanted_series.lower()):
                if wanted_season == season_num and wanted_episode == episode_num:
                    logger.info(f"Found match: {series_title} S{season_num:02d}E{episode_num:02d}")
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking episode in wanted list: {e}")
        return False

def get_recent_history_entries(cutoff_date: datetime) -> List[str]:
    """Get history entry file paths that are newer than cutoff_date"""
    try:
        ensure_history_dir()
        history_entries = []
        
        # Walk through all history files in the base directory
        for root, dirs, files in os.walk(HISTORY_BASE_PATH):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime >= cutoff_date:
                            history_entries.append(file_path)
                    except Exception as e:
                        logger.debug(f"Error checking file time for {file_path}: {e}")
                        continue
        
        logger.info(f"Found {len(history_entries)} recent history files")
        return history_entries
        
    except Exception as e:
        logger.error(f"Error getting recent history entries: {e}")
        return []

def get_undiscovered_entries() -> List[Dict[str, Any]]:
    """
    Get all undiscovered history entries from the last N days for Sonarr
    
    Returns:
        List of undiscovered entries with file path info
    """
    undiscovered_entries = []
    hunting_config = get_hunting_config()
    days_back = hunting_config.get('discovery_check_days_back', 7)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        # Ensure history directory exists
        ensure_history_dir()
        
        # Check Sonarr history files
        sonarr_history_dir = HISTORY_BASE_PATH / "sonarr"
        
        if not sonarr_history_dir.exists():
            logger.debug("No Sonarr history directory found")
            return undiscovered_entries
        
        # Process each JSON file in sonarr directory
        for history_file in sonarr_history_dir.glob("*.json"):
            try:
                with open(history_file, 'r') as f:
                    entries = json.load(f)
                
                if not isinstance(entries, list):
                    continue
                
                for i, entry in enumerate(entries):
                    # Skip if already discovered
                    if entry.get('discovered', False):
                        continue
                    
                    # Skip if not missing operation
                    if entry.get('operation_type') != 'missing':
                        continue
                    
                    # Skip if too old
                    entry_date = datetime.fromtimestamp(entry.get('date_time', 0))
                    if entry_date < cutoff_date:
                        continue
                    
                    # Add file info for updating later
                    entry['_file_path'] = str(history_file)
                    entry['_entry_index'] = i
                    undiscovered_entries.append(entry)
                    
            except Exception as e:
                logger.error(f"Error processing history file {history_file}: {e}")
                continue
        
        logger.info(f"Found {len(undiscovered_entries)} undiscovered entries to check")
        return undiscovered_entries
        
    except Exception as e:
        logger.error(f"Error getting undiscovered entries: {e}")
        return []

def update_history_entry_discovered(file_path: str, entry_index: int, discovered: bool = True):
    """
    Update a specific history entry to mark it as discovered
    
    Args:
        file_path: Path to the history file
        entry_index: Index of the entry in the file
        discovered: Whether the item was discovered (default True)
    """
    try:
        with open(file_path, 'r') as f:
            entries = json.load(f)
        
        if 0 <= entry_index < len(entries):
            entries[entry_index]['discovered'] = discovered
            
            with open(file_path, 'w') as f:
                json.dump(entries, f, indent=2)
            
            logger.debug(f"Updated entry {entry_index} in {file_path} - discovered: {discovered}")
        
    except Exception as e:
        logger.error(f"Error updating history entry {entry_index} in {file_path}: {e}")

def perform_discovery_check():
    """Perform a discovery check on recent history entries"""
    try:
        config = get_hunting_config()
        if not config.get("enabled", True):
            logger.info("Discovery tracking is disabled")
            return
        
        days_back = config.get("discovery_check_days_back", 7)
        logger.info(f"Starting discovery check for entries from the last {days_back} days")
        
        # Get Sonarr instances
        sonarr_instances = get_sonarr_instances()
        if not sonarr_instances:
            logger.warning("No Sonarr instances configured")
            return
        
        # Get enabled instances only
        enabled_instances = [inst for inst in sonarr_instances if inst.get("enabled", True)]
        if not enabled_instances:
            logger.warning("No enabled Sonarr instances found")
            return
        
        logger.info(f"Found {len(enabled_instances)} enabled Sonarr instance(s)")
        
        # Get wanted episodes from all enabled Sonarr instances
        all_wanted_episodes = []
        for instance in enabled_instances:
            wanted_episodes = get_sonarr_wanted_episodes(instance)
            all_wanted_episodes.extend(wanted_episodes)
        
        if not all_wanted_episodes:
            logger.info("No wanted episodes found in any Sonarr instance")
            return
        
        logger.info(f"Total wanted episodes across all instances: {len(all_wanted_episodes)}")
        
        # Get recent history entries
        cutoff_date = datetime.now() - timedelta(days=days_back)
        history_entry_files = get_recent_history_entries(cutoff_date)
        
        discovered_count = 0
        checked_count = 0
        error_count = 0
        
        for entry_path in history_entry_files:
            try:
                checked_count += 1
                
                # Load history entry
                with open(entry_path, 'r') as f:
                    entry_data = json.load(f)
                
                # Handle both single entries and arrays of entries
                entries_to_check = []
                if isinstance(entry_data, list):
                    entries_to_check = entry_data
                else:
                    entries_to_check = [entry_data]
                
                file_modified = False
                for i, entry in enumerate(entries_to_check):
                    # Skip if already discovered
                    if entry.get("discovered", False):
                        continue
                    
                    # Check if this episode is now in the wanted list
                    if check_episode_in_wanted(entry, all_wanted_episodes):
                        # Mark as discovered
                        entry["discovered"] = True
                        entry["discovered_at"] = datetime.now().isoformat()
                        file_modified = True
                        discovered_count += 1
                        logger.info(f"Discovered episode: {entry.get('series_title', 'Unknown')} - {entry.get('episode_title', 'Unknown')}")
                
                # Save file if it was modified
                if file_modified:
                    with open(entry_path, 'w') as f:
                        if isinstance(entry_data, list):
                            json.dump(entries_to_check, f, indent=2)
                        else:
                            json.dump(entries_to_check[0], f, indent=2)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing history entry {entry_path}: {e}")
        
        logger.info(f"Discovery check complete: {checked_count} entries checked, {discovered_count} discovered, {error_count} errors/stopped")
        
    except Exception as e:
        logger.error(f"Error in discovery check: {e}")

def discovery_thread():
    """
    Main discovery thread function
    """
    try:
        while not _discovery_stop_event.is_set():
            perform_discovery_check()
            time.sleep(60 * get_hunting_config().get('discovery_check_interval_minutes', 10))
    except Exception as e:
        logger.error(f"Discovery thread error: {e}")

def start_discovery_scheduler():
    """
    Start the independent discovery tracking scheduler
    """
    try:
        hunting_config = get_hunting_config()
        if not hunting_config.get('enabled', True):
            logger.info("Discovery tracking is disabled in configuration")
            return
        
        logger.info(f"Starting Hunt Manager - discovery checks every {hunting_config.get('discovery_check_interval_minutes', 10)} minutes")
        
        global _discovery_thread
        _discovery_thread = threading.Thread(target=discovery_thread, daemon=True)
        _discovery_thread.start()
        
    except Exception as e:
        logger.error(f"Error in discovery scheduler: {e}")

def run_discovery_tracker_background():
    """
    Run discovery tracker in background thread
    """
    start_discovery_scheduler()
    logger.info("Hunt Manager started in background thread")

if __name__ == "__main__":
    # For testing
    start_discovery_scheduler()
