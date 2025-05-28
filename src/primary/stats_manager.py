#!/usr/bin/env python3
"""
Statistics Manager for Huntarr
Handles tracking, storing, and retrieving statistics about hunted and upgraded media
and monitoring hourly API usage for rate limiting
"""

import os
import json
import time
import datetime
import threading
from typing import Dict, Any, Optional
from src.primary.utils.logger import get_logger
from src.primary.settings_manager import get_advanced_setting
# Import centralized path configuration
from src.primary.utils.config_paths import CONFIG_PATH

logger = get_logger("stats")

# Path constants - Define multiple possible locations and check them in order using centralized config
STATS_DIRS = [
    os.path.join(str(CONFIG_PATH), "tally"),                 # Main cross-platform config path
    os.path.join(os.path.expanduser("~"), ".huntarr/tally"), # User's home directory (fallback)
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data/tally") # Relative to script (fallback)
]

# Lock for thread-safe operations
stats_lock = threading.Lock()
hourly_lock = threading.Lock()

def find_writable_stats_dir():
    """Find a writable directory for stats from the list of candidates"""
    for dir_path in STATS_DIRS:
        try:
            os.makedirs(dir_path, exist_ok=True)
            test_file = os.path.join(dir_path, "write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Using stats directory: {dir_path}")
            return dir_path
        except (IOError, OSError) as e:
            logger.warning(f"Directory {dir_path} is not writable: {e}")
            continue
    
    # Fallback to current directory
    fallback_dir = os.path.join(os.getcwd(), "tally")
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        logger.info(f"Falling back to current directory for stats: {fallback_dir}")
        return fallback_dir
    except Exception as e:
        logger.error(f"Failed to create fallback stats directory: {e}")
        return None

# Find the best stats directory
STATS_DIR = find_writable_stats_dir()
STATS_FILE = os.path.join(STATS_DIR, "media_stats.json") if STATS_DIR else None
HOURLY_CAP_FILE = os.path.join(STATS_DIR, "hourly_cap.json") if STATS_DIR else None

# Log the stats file location once at module load time
if STATS_FILE:
    logger.info(f"===> Stats will be stored at: {STATS_FILE}")
    logger.info(f"===> Hourly API cap tracking will be stored at: {HOURLY_CAP_FILE}")
else:
    logger.error("===> CRITICAL: No stats file location could be determined!")

# Store the last hour we checked for resetting hourly caps
last_hour_checked = None

# Schedule the next hourly reset check
next_reset_check = None

def ensure_stats_dir():
    """Ensure the statistics directory exists"""
    if not STATS_DIR:
        logger.error("No writable stats directory found")
        return False
    
    try:
        os.makedirs(STATS_DIR, exist_ok=True)
        logger.debug(f"Stats directory ensured: {STATS_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create stats directory: {e}")
        return False

def load_stats() -> Dict[str, Dict[str, int]]:
    """
    Load statistics from the stats file
    
    Returns:
        Dictionary containing statistics for each app
    """
    if not ensure_stats_dir() or not STATS_FILE:
        logger.error("Cannot load stats - no valid stats directory available")
        return get_default_stats()
    
    default_stats = get_default_stats()
    
    try:
        if os.path.exists(STATS_FILE):
            logger.debug(f"Loading stats from: {STATS_FILE}")
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                
            # Ensure all apps are in the stats
            for app in default_stats:
                if app not in stats:
                    stats[app] = default_stats[app]
            
            logger.debug(f"Loaded stats: {stats}")
            return stats
        else:
            logger.info(f"Stats file not found at {STATS_FILE}, using default stats")
        return default_stats
    except Exception as e:
        logger.error(f"Error loading stats from {STATS_FILE}: {e}")
        return default_stats

def get_default_stats() -> Dict[str, Dict[str, int]]:
    """Get the default stats structure"""
    return {
        "sonarr": {"hunted": 0, "upgraded": 0},
        "radarr": {"hunted": 0, "upgraded": 0},
        "lidarr": {"hunted": 0, "upgraded": 0},
        "readarr": {"hunted": 0, "upgraded": 0},
        "whisparr": {"hunted": 0, "upgraded": 0},
        "eros": {"hunted": 0, "upgraded": 0},
        "swaparr": {"hunted": 0, "upgraded": 0}
    }

def get_default_hourly_caps() -> Dict[str, Dict[str, int]]:
    """Get the default hourly caps structure"""
    return {
        "sonarr": {"api_hits": 0},
        "radarr": {"api_hits": 0},
        "lidarr": {"api_hits": 0},
        "readarr": {"api_hits": 0},
        "whisparr": {"api_hits": 0},
        "eros": {"api_hits": 0}
    }

def load_hourly_caps() -> Dict[str, Dict[str, int]]:
    """
    Load hourly API caps from the caps file
    
    Returns:
        Dictionary containing hourly API usage for each app
    """
    if not ensure_stats_dir() or not HOURLY_CAP_FILE:
        logger.error("Cannot load hourly caps - no valid stats directory available")
        return get_default_hourly_caps()
    
    default_caps = get_default_hourly_caps()
    
    try:
        if os.path.exists(HOURLY_CAP_FILE):
            logger.debug(f"Loading hourly caps from: {HOURLY_CAP_FILE}")
            with open(HOURLY_CAP_FILE, 'r') as f:
                caps = json.load(f)
                
            # Ensure all apps are in the caps
            for app in default_caps:
                if app not in caps:
                    caps[app] = default_caps[app]
            
            logger.debug(f"Loaded hourly caps: {caps}")
            return caps
        else:
            logger.info(f"Hourly caps file not found at {HOURLY_CAP_FILE}, using default caps")
            return default_caps
    except Exception as e:
        logger.error(f"Error loading hourly caps from {HOURLY_CAP_FILE}: {e}")
        return default_caps

def save_hourly_caps(caps: Dict[str, Dict[str, int]]) -> bool:
    """
    Save hourly API caps to the caps file
    
    Args:
        caps: Dictionary containing hourly API usage for each app
        
    Returns:
        True if successful, False otherwise
    """
    if not ensure_stats_dir() or not HOURLY_CAP_FILE:
        logger.error("Cannot save hourly caps - no valid stats directory available")
        return False
    
    try:
        logger.debug(f"Saving hourly caps to: {HOURLY_CAP_FILE}")
        # First write to a temp file, then move it to avoid partial writes
        temp_file = f"{HOURLY_CAP_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(caps, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Move the temp file to the actual file
        os.replace(temp_file, HOURLY_CAP_FILE)
        
        logger.debug(f"Hourly caps saved successfully: {caps}")
        return True
    except Exception as e:
        logger.error(f"Error saving hourly caps to {HOURLY_CAP_FILE}: {e}", exc_info=True)
        return False

def reset_hourly_caps() -> bool:
    """
    Reset all hourly API caps to zero at the top of the hour
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=== RESETTING HOURLY API CAPS ===")
    try:
        if os.path.exists(HOURLY_CAP_FILE):
            os.remove(HOURLY_CAP_FILE)
            logger.info(f"Deleted hourly caps file at {HOURLY_CAP_FILE} to reset all API caps")
            
        # Create a fresh hourly caps file
        caps = get_default_hourly_caps()
        save_success = save_hourly_caps(caps)
        
        if save_success:
            logger.info("Successfully reset all hourly API caps to zero")
            return True
        else:
            logger.error("Failed to save reset hourly caps")
            return False
    except Exception as e:
        logger.error(f"Error resetting hourly API caps: {e}")
        return False

def check_hourly_reset():
    """
    Check if we need to reset hourly caps based on the current hour
    """
    global last_hour_checked, next_reset_check
    
    current_time = datetime.datetime.now()
    current_hour = current_time.hour
    
    # Skip if we've already checked this hour
    if last_hour_checked == current_hour:
        return
    
    # Only reset at the top of the hour (00 minute mark)
    if current_time.minute == 0:
        logger.info(f"Hour changed to {current_hour}:00, resetting hourly API caps")
        reset_hourly_caps()
        last_hour_checked = current_hour

def increment_hourly_cap(app_type: str, count: int = 1) -> bool:
    """
    Increment hourly API usage cap for a specific app
    
    Args:
        app_type: The application type (sonarr, radarr, etc.)
        count: The amount to increment by (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    if app_type not in ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros"]:
        logger.error(f"Invalid app_type for hourly cap: {app_type}")
        return False
    
    # Check if we need to reset hourly caps
    check_hourly_reset()
    
    with hourly_lock:
        caps = load_hourly_caps()
        prev_value = caps[app_type]["api_hits"]
        caps[app_type]["api_hits"] += count
        new_value = caps[app_type]["api_hits"]
        
        # Get the hourly cap from the app's specific configuration
        from src.primary.settings_manager import load_settings
        app_settings = load_settings(app_type)
        hourly_limit = app_settings.get("hourly_cap", 20)  # Default to 20 if not set
        
        # Log current usage vs limit
        logger.debug(f"*** HOURLY API INCREMENT *** {app_type} by {count}: {prev_value} -> {new_value} (limit: {hourly_limit})")
        
        # Warn if approaching limit
        if new_value >= int(hourly_limit * 0.8) and prev_value < int(hourly_limit * 0.8):
            logger.warning(f"{app_type} is approaching hourly API cap: {new_value}/{hourly_limit}")
        
        # Alert if exceeding limit
        if new_value >= hourly_limit and prev_value < hourly_limit:
            logger.error(f"{app_type} has exceeded hourly API cap: {new_value}/{hourly_limit}")
        
        save_success = save_hourly_caps(caps)
        
        if not save_success:
            logger.error(f"Failed to save hourly caps after incrementing {app_type}")
            return False
            
        return True

def get_hourly_cap_status(app_type: str) -> Dict[str, Any]:
    """
    Get current API usage status for an app
    
    Args:
        app_type: The application type (sonarr, radarr, etc.)
        
    Returns:
        Dictionary with usage information
    """
    if app_type not in ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros"]:
        return {"error": f"Invalid app_type: {app_type}"}
    
    with hourly_lock:
        caps = load_hourly_caps()
        
        # Get the hourly cap from the app's specific configuration
        from src.primary.settings_manager import load_settings
        app_settings = load_settings(app_type)
        hourly_limit = app_settings.get("hourly_cap", 20)  # Default to 20 if not set
        
        current_usage = caps[app_type]["api_hits"]
        
        return {
            "app": app_type,
            "current_usage": current_usage,
            "limit": hourly_limit,
            "remaining": max(0, hourly_limit - current_usage),
            "percent_used": int((current_usage / hourly_limit) * 100) if hourly_limit > 0 else 0,
            "exceeded": current_usage >= hourly_limit
        }

def check_hourly_cap_exceeded(app_type: str) -> bool:
    """
    Check if an app has exceeded its hourly API cap
    
    Args:
        app_type: The application type (sonarr, radarr, etc.)
        
    Returns:
        True if exceeded, False otherwise
    """
    status = get_hourly_cap_status(app_type)
    return status.get("exceeded", False)

def save_stats(stats: Dict[str, Dict[str, int]]) -> bool:
    """
    Save statistics to the stats file
    
    Args:
        stats: Dictionary containing statistics for each app
        
    Returns:
        True if successful, False otherwise
    """
    if not ensure_stats_dir() or not STATS_FILE:
        logger.error("Cannot save stats - no valid stats directory available")
        return False
    
    try:
        logger.debug(f"Saving stats to: {STATS_FILE}")
        # First write to a temp file, then move it to avoid partial writes
        temp_file = f"{STATS_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(stats, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Move the temp file to the actual file
        os.replace(temp_file, STATS_FILE)
        
        logger.info(f"===> Successfully wrote stats to file: {STATS_FILE}")
        logger.debug(f"Stats saved successfully: {stats}")
        return True
    except Exception as e:
        logger.error(f"Error saving stats to {STATS_FILE}: {e}", exc_info=True)
        return False

def increment_stat(app_type: str, stat_type: str, count: int = 1) -> bool:
    """
    Increment a specific statistic
    
    Args:
        app_type: The application type (sonarr, radarr, etc.)
        stat_type: The type of statistic (hunted or upgraded)
        count: The amount to increment by (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    if app_type not in ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros", "swaparr"]:
        logger.error(f"Invalid app_type: {app_type}")
        return False
        
    if stat_type not in ["hunted", "upgraded"]:
        logger.error(f"Invalid stat_type: {stat_type}")
        return False
    
    # Also increment the hourly API cap for this app, unless it's swaparr which doesn't have an API
    if app_type != "swaparr":
        increment_hourly_cap(app_type, count)
    
    with stats_lock:
        stats = load_stats()
        prev_value = stats[app_type][stat_type]
        stats[app_type][stat_type] += count
        new_value = stats[app_type][stat_type]
        logger.debug(f"*** STATS INCREMENT *** {app_type} {stat_type} by {count}: {prev_value} -> {new_value}")
        save_success = save_stats(stats)
        
        if not save_success:
            logger.error(f"Failed to save stats after incrementing {app_type} {stat_type}")
            return False
            
        # Add debug verification that stats were actually saved
        verification_stats = load_stats()
        if verification_stats[app_type][stat_type] != new_value:
            logger.error(f"Stats verification failed! Expected {new_value} but got {verification_stats[app_type][stat_type]} for {app_type} {stat_type}")
            return False
            
        logger.debug(f"Successfully incremented and verified {app_type} {stat_type}")
        return True

def increment_stat_only(app_type: str, stat_type: str, count: int = 1) -> bool:
    """
    Increment a specific statistic WITHOUT incrementing API cap counter
    
    This function is specifically for season packs where the API call is already tracked
    separately and we only want to increment the stats for each episode.
    
    Args:
        app_type: The application type (sonarr, radarr, etc.)
        stat_type: The type of statistic (hunted or upgraded)
        count: The amount to increment by (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    if app_type not in ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros", "swaparr"]:
        logger.error(f"Invalid app_type: {app_type}")
        return False
        
    if stat_type not in ["hunted", "upgraded"]:
        logger.error(f"Invalid stat_type: {stat_type}")
        return False
    
    # CRITICAL: Do NOT increment hourly API cap - this is for season packs where
    # the API call is already tracked separately in search_season()
    
    with stats_lock:
        stats = load_stats()
        prev_value = stats[app_type][stat_type]
        stats[app_type][stat_type] += count
        new_value = stats[app_type][stat_type]
        logger.debug(f"*** STATS ONLY INCREMENT *** {app_type} {stat_type} by {count}: {prev_value} -> {new_value} (API cap NOT incremented)")
        save_success = save_stats(stats)
        
        if not save_success:
            logger.error(f"Failed to save stats after incrementing {app_type} {stat_type}")
            return False
            
        # Add debug verification that stats were actually saved
        verification_stats = load_stats()
        if verification_stats[app_type][stat_type] != new_value:
            logger.error(f"Stats verification failed! Expected {new_value} but got {verification_stats[app_type][stat_type]} for {app_type} {stat_type}")
            return False
            
        logger.debug(f"Successfully incremented and verified {app_type} {stat_type} (stats only)")
        return True

def get_stats() -> Dict[str, Dict[str, int]]:
    """
    Get the current statistics
    
    Returns:
        Dictionary containing statistics for each app
    """
    with stats_lock:
        stats = load_stats()
        logger.debug(f"Retrieved stats: {stats}")
        return stats

def reset_stats(app_type: Optional[str] = None) -> bool:
    """
    Reset statistics for a specific app or all apps
    
    Args:
        app_type: The application type to reset, or None to reset all
        
    Returns:
        True if successful, False otherwise
    """
    with stats_lock:
        stats = load_stats()
        
        if app_type is None:
            # Reset all stats
            logger.info("Resetting all app statistics")
            for app in stats:
                stats[app]["hunted"] = 0
                stats[app]["upgraded"] = 0
        elif app_type in stats:
            # Reset specific app stats
            logger.info(f"Resetting statistics for {app_type}")
            stats[app_type]["hunted"] = 0
            stats[app_type]["upgraded"] = 0
        else:
            logger.error(f"Invalid app_type for reset: {app_type}")
            return False
            
        return save_stats(stats)

# Initialize the files with find_writable_stats_dir already called during import
if STATS_DIR:
    # Initialize stats file if it doesn't exist
    if not os.path.exists(STATS_FILE):
        logger.info(f"Creating new stats file at: {STATS_FILE}")
        save_stats(get_default_stats())
        
    # Initialize hourly caps file if it doesn't exist
    if not os.path.exists(HOURLY_CAP_FILE):
        logger.info(f"Creating new hourly caps file at: {HOURLY_CAP_FILE}")
        save_hourly_caps(get_default_hourly_caps())
    
    # Set up the initial hour check
    last_hour_checked = datetime.datetime.now().hour
else:
    logger.debug(f"Stats system initialized. Using file: {STATS_FILE}")