#!/usr/bin/env python3
"""
Swaparr Statistics Manager
Handles tracking, storing, and retrieving Swaparr-specific statistics
"""

import os
import json
import threading
from typing import Dict, Any
from src.primary.utils.logger import get_logger
from src.primary.utils.config_paths import CONFIG_PATH

logger = get_logger("swaparr_stats")

# Path for Swaparr stats
SWAPARR_STATS_DIR = os.path.join(str(CONFIG_PATH), "tally")
SWAPARR_STATS_FILE = os.path.join(SWAPARR_STATS_DIR, "swaparr_stats.json")

# Lock for thread-safe operations
swaparr_stats_lock = threading.Lock()

def ensure_swaparr_stats_dir():
    """Ensure the Swaparr statistics directory exists"""
    try:
        os.makedirs(SWAPARR_STATS_DIR, exist_ok=True)
        logger.debug(f"Swaparr stats directory ensured: {SWAPARR_STATS_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Swaparr stats directory: {e}")
        return False

def get_default_swaparr_stats() -> Dict[str, int]:
    """Get the default Swaparr stats structure"""
    return {
        "processed": 0,
        "strikes": 0,
        "removals": 0,
        "ignored": 0
    }

def load_swaparr_stats() -> Dict[str, int]:
    """
    Load Swaparr statistics from the stats file
    
    Returns:
        Dictionary containing Swaparr statistics
    """
    if not ensure_swaparr_stats_dir():
        logger.error("Cannot load Swaparr stats - no valid stats directory available")
        return get_default_swaparr_stats()
    
    default_stats = get_default_swaparr_stats()
    
    try:
        if os.path.exists(SWAPARR_STATS_FILE):
            logger.debug(f"Loading Swaparr stats from: {SWAPARR_STATS_FILE}")
            with open(SWAPARR_STATS_FILE, 'r') as f:
                stats = json.load(f)
                
            # Ensure all expected keys are present
            for key in default_stats:
                if key not in stats:
                    stats[key] = default_stats[key]
            
            logger.debug(f"Loaded Swaparr stats: {stats}")
            return stats
        else:
            logger.info(f"Swaparr stats file not found at {SWAPARR_STATS_FILE}, using default stats")
        return default_stats
    except Exception as e:
        logger.error(f"Error loading Swaparr stats from {SWAPARR_STATS_FILE}: {e}")
        return default_stats

def save_swaparr_stats(stats: Dict[str, int]) -> bool:
    """
    Save Swaparr statistics to the stats file
    
    Args:
        stats: Dictionary containing Swaparr statistics
        
    Returns:
        True if successful, False otherwise
    """
    if not ensure_swaparr_stats_dir():
        logger.error("Cannot save Swaparr stats - no valid stats directory available")
        return False
    
    try:
        logger.debug(f"Saving Swaparr stats to: {SWAPARR_STATS_FILE}")
        # First write to a temp file, then move it to avoid partial writes
        temp_file = f"{SWAPARR_STATS_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(stats, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Move the temp file to the actual file
        os.rename(temp_file, SWAPARR_STATS_FILE)
        logger.debug("Swaparr stats saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving Swaparr stats to {SWAPARR_STATS_FILE}: {e}")
        return False

def increment_swaparr_stat(stat_type: str, count: int = 1) -> bool:
    """
    Increment a Swaparr statistic by the specified count
    
    Args:
        stat_type: Type of stat to increment ('processed', 'strikes', 'removals', 'ignored')
        count: Amount to increment by (default 1)
        
    Returns:
        True if successful, False otherwise
    """
    valid_stats = ['processed', 'strikes', 'removals', 'ignored']
    if stat_type not in valid_stats:
        logger.error(f"Invalid Swaparr stat type: {stat_type}. Valid types: {valid_stats}")
        return False
    
    with swaparr_stats_lock:
        try:
            stats = load_swaparr_stats()
            stats[stat_type] += count
            
            success = save_swaparr_stats(stats)
            if success:
                logger.debug(f"Incremented Swaparr {stat_type} by {count}. New value: {stats[stat_type]}")
            return success
        except Exception as e:
            logger.error(f"Error incrementing Swaparr {stat_type}: {e}")
            return False

def get_swaparr_stats() -> Dict[str, int]:
    """
    Get current Swaparr statistics
    
    Returns:
        Dictionary containing current Swaparr statistics
    """
    with swaparr_stats_lock:
        return load_swaparr_stats()

def reset_swaparr_stats() -> bool:
    """
    Reset all Swaparr statistics to zero
    
    Returns:
        True if successful, False otherwise
    """
    with swaparr_stats_lock:
        try:
            default_stats = get_default_swaparr_stats()
            success = save_swaparr_stats(default_stats)
            if success:
                logger.info("Reset all Swaparr statistics to zero")
            return success
        except Exception as e:
            logger.error(f"Error resetting Swaparr stats: {e}")
            return False 