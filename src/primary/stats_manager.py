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

# Path constants
STATS_DIR = "/config/tally"
STATS_FILE = os.path.join(STATS_DIR, "media_stats.json")

# Lock for thread-safe operations
stats_lock = threading.Lock()

def ensure_stats_dir():
    """Ensure the statistics directory exists"""
    try:
        os.makedirs(STATS_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create stats directory: {e}")

def load_stats() -> Dict[str, Dict[str, int]]:
    """
    Load statistics from the stats file
    
    Returns:
        Dictionary containing statistics for each app
    """
    ensure_stats_dir()
    
    default_stats = {
        "sonarr": {"hunted": 0, "upgraded": 0},
        "radarr": {"hunted": 0, "upgraded": 0},
        "lidarr": {"hunted": 0, "upgraded": 0},
        "readarr": {"hunted": 0, "upgraded": 0},
        "whisparr": {"hunted": 0, "upgraded": 0}
    }
    
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                
            # Ensure all apps are in the stats
            for app in default_stats:
                if app not in stats:
                    stats[app] = default_stats[app]
                    
            return stats
        return default_stats
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
        return default_stats

def save_stats(stats: Dict[str, Dict[str, int]]) -> bool:
    """
    Save statistics to the stats file
    
    Args:
        stats: Dictionary containing statistics for each app
        
    Returns:
        True if successful, False otherwise
    """
    ensure_stats_dir()
    
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving stats: {e}")
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
    if app_type not in ["sonarr", "radarr", "lidarr", "readarr", "whisparr"]:
        logger.error(f"Invalid app_type: {app_type}")
        return False
        
    if stat_type not in ["hunted", "upgraded"]:
        logger.error(f"Invalid stat_type: {stat_type}")
        return False
    
    with stats_lock:
        stats = load_stats()
        stats[app_type][stat_type] += count
        return save_stats(stats)

def get_stats() -> Dict[str, Dict[str, int]]:
    """
    Get the current statistics
    
    Returns:
        Dictionary containing statistics for each app
    """
    with stats_lock:
        return load_stats()

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
            for app in stats:
                stats[app]["hunted"] = 0
                stats[app]["upgraded"] = 0
        elif app_type in stats:
            # Reset specific app stats
            stats[app_type]["hunted"] = 0
            stats[app_type]["upgraded"] = 0
        else:
            logger.error(f"Invalid app_type: {app_type}")
            return False
            
        return save_stats(stats)

# Initialize stats file if it doesn't exist
ensure_stats_dir()
if not os.path.exists(STATS_FILE):
    default_stats = {
        "sonarr": {"hunted": 0, "upgraded": 0},
        "radarr": {"hunted": 0, "upgraded": 0},
        "lidarr": {"hunted": 0, "upgraded": 0},
        "readarr": {"hunted": 0, "upgraded": 0},
        "whisparr": {"hunted": 0, "upgraded": 0}
    }
    save_stats(default_stats)