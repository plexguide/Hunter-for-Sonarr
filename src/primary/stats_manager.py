#!/usr/bin/env python3
"""
Statistics Manager for Huntarr
Handles tracking, storing, and retrieving statistics about hunted and upgraded media
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional
from src.primary.utils.logger import get_logger

logger = get_logger("stats")

# Path constants - Define multiple possible locations and check them in order
STATS_DIRS = [
    "/config/tally",                                        # Docker default
    os.path.join(os.path.expanduser("~"), ".huntarr/tally"), # User's home directory
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data/tally") # Relative to script
]

# Lock for thread-safe operations
stats_lock = threading.Lock()

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

# Log the stats file location once at module load time
if STATS_FILE:
    logger.info(f"===> Stats will be stored at: {STATS_FILE}")
else:
    logger.error("===> CRITICAL: No stats file location could be determined!")

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
    
    with stats_lock:
        stats = load_stats()
        prev_value = stats[app_type][stat_type]
        stats[app_type][stat_type] += count
        new_value = stats[app_type][stat_type]
        logger.info(f"*** STATS INCREMENT *** {app_type} {stat_type} by {count}: {prev_value} -> {new_value}")
        save_success = save_stats(stats)
        
        if not save_success:
            logger.error(f"Failed to save stats after incrementing {app_type} {stat_type}")
            return False
            
        # Add debug verification that stats were actually saved
        verification_stats = load_stats()
        if verification_stats[app_type][stat_type] != new_value:
            logger.error(f"Stats verification failed! Expected {new_value} but got {verification_stats[app_type][stat_type]} for {app_type} {stat_type}")
            return False
            
        logger.info(f"Successfully incremented and verified {app_type} {stat_type}")
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

# Initialize stats file with find_writable_stats_dir already called during import
if STATS_DIR and not os.path.exists(STATS_FILE):
    logger.info(f"Creating new stats file at: {STATS_FILE}")
    save_stats(get_default_stats())
else:
    logger.debug(f"Stats system initialized. Using file: {STATS_FILE}")