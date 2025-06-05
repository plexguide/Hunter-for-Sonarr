#!/usr/bin/env python3
"""
Clean logging system for frontend consumption
Creates clean, stripped log messages without redundant information
"""

import logging
import time
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pytz

# Use the centralized path configuration
from src.primary.utils.config_paths import LOG_DIR

# Clean log files for frontend consumption
CLEAN_LOG_FILES = {
    "system": LOG_DIR / "clean_huntarr.log",
    "sonarr": LOG_DIR / "clean_sonarr.log",
    "radarr": LOG_DIR / "clean_radarr.log",
    "lidarr": LOG_DIR / "clean_lidarr.log", 
    "readarr": LOG_DIR / "clean_readarr.log",
    "whisparr": LOG_DIR / "clean_whisparr.log",
    "eros": LOG_DIR / "clean_eros.log",
    "swaparr": LOG_DIR / "clean_swaparr.log",
    "hunting": LOG_DIR / "clean_hunting.log"
}

def _get_user_timezone():
    """Get the user's selected timezone from general settings"""
    try:
        from src.primary import settings_manager
        general_settings = settings_manager.load_settings("general")
        timezone_name = general_settings.get("timezone", "UTC")
        
        try:
            return pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            return pytz.UTC
    except Exception:
        return pytz.UTC

class CleanLogFormatter(logging.Formatter):
    """
    Custom formatter that creates clean log messages for frontend consumption.
    Uses pipe separators for easy parsing: timestamp|level|app_type|message
    """
    
    def __init__(self):
        # No format needed as we'll build it manually
        super().__init__()
    
    def format(self, record):
        """
        Format the log record as: timestamp|level|app_type|clean_message
        This format makes it easy for frontend to parse and display properly.
        """
        # Get the original formatted message
        original_message = record.getMessage()
        
        # Clean the message by removing redundant information
        clean_message = self._clean_message(original_message, record.name, record.levelname)
        
        # Format timestamp using user's configured timezone
        timestamp = self._format_timestamp_with_user_timezone(record.created)
        
        # Determine app type from logger name
        app_type = self._get_app_type(record.name)
        
        # Format as: timestamp|level|app_type|message
        return f"{timestamp}|{record.levelname}|{app_type}|{clean_message}"
    
    def _format_timestamp_with_user_timezone(self, timestamp):
        """
        Format timestamp using the user's configured timezone from settings.
        """
        try:
            # Get user's configured timezone
            user_tz = _get_user_timezone()
            
            # Convert UTC timestamp to user's timezone
            utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
            local_dt = utc_dt.astimezone(user_tz)
            
            # Format without timezone abbreviation for cleaner display
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            # Fallback to UTC if anything goes wrong
            return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
    
    def _clean_message(self, message: str, logger_name: str, level: str) -> str:
        """
        Clean a log message by removing redundant information.
        
        Args:
            message: Original log message
            logger_name: Name of the logger (e.g., 'huntarr.sonarr')
            level: Log level (DEBUG, INFO, etc.)
            
        Returns:
            Cleaned message with redundant information removed
        """
        clean_msg = message
        
        # Remove timestamp patterns at the beginning
        # Patterns: YYYY-MM-DD HH:MM:SS [Timezone]
        clean_msg = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\s+[A-Za-z_/]+)?\s*-\s*', '', clean_msg)
        
        # Remove logger name patterns
        # e.g., "huntarr.sonarr - DEBUG -" or "huntarr -"
        logger_pattern = logger_name.replace('.', r'\.')
        clean_msg = re.sub(f'^{logger_pattern}\\s*-\\s*{level}\\s*-\\s*', '', clean_msg)
        clean_msg = re.sub(f'^{logger_pattern}\\s*-\\s*', '', clean_msg)
        
        # Remove common redundant prefixes
        prefixes_to_remove = [
            r'^huntarr\.[a-zA-Z]+\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*',
            r'^huntarr\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*',
            r'^huntarr\.[a-zA-Z]+\s*-\s*',
            r'^huntarr\s*-\s*',
            r'^\[system\]\s*',
            r'^\[sonarr\]\s*',
            r'^\[radarr\]\s*',
            r'^\[lidarr\]\s*',
            r'^\[readarr\]\s*',
            r'^\[whisparr\]\s*',
            r'^\[eros\]\s*',
            r'^\[hunting\]\s*',
        ]
        
        for pattern in prefixes_to_remove:
            clean_msg = re.sub(pattern, '', clean_msg, flags=re.IGNORECASE)
        
        # Remove any remaining timestamp patterns that might be in the middle
        clean_msg = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\s+[A-Za-z_/]+)?\s*-\s*', '', clean_msg)
        
        # Clean up extra whitespace and dashes
        clean_msg = re.sub(r'^\s*-\s*', '', clean_msg)  # Remove leading dashes
        clean_msg = re.sub(r'\s+', ' ', clean_msg)      # Normalize whitespace
        clean_msg = clean_msg.strip()                   # Remove leading/trailing whitespace
        
        # If the message is empty after cleaning, provide a fallback
        if not clean_msg:
            clean_msg = "Log message"
            
        return clean_msg
    
    def _get_app_type(self, logger_name: str) -> str:
        """
        Determine the app type from the logger name.
        
        Args:
            logger_name: Name of the logger (e.g., 'huntarr.sonarr')
            
        Returns:
            App type (e.g., 'sonarr', 'system')
        """
        # Remove 'huntarr.' prefix if present
        if logger_name.startswith('huntarr.'):
            logger_name = logger_name[8:]
        
        # Map logger name to app type
        app_types = {
            'sonarr': 'sonarr',
            'radarr': 'radarr',
            'lidarr': 'lidarr',
            'readarr': 'readarr',
            'whisparr': 'whisparr',
            'eros': 'eros',
            'swaparr': 'swaparr',
            'hunting': 'hunting',
        }
        
        return app_types.get(logger_name, 'system')


class CleanLogHandler(logging.Handler):
    """
    Custom log handler that writes clean log messages to separate files.
    """
    
    def __init__(self, log_file_path: Path):
        super().__init__()
        self.log_file_path = log_file_path
        self.setFormatter(CleanLogFormatter())
        
        # Ensure the log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, record):
        """Write the log record to the clean log file."""
        try:
            msg = self.format(record)
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            self.handleError(record)


# Global clean handlers registry
_clean_handlers: Dict[str, CleanLogHandler] = {}


def setup_clean_logging():
    """
    Set up clean logging handlers for all known logger types.
    This should be called once during application startup.
    """
    from src.primary.utils.logger import get_logger
    
    # Set up clean handlers for each app type
    for app_type, clean_log_file in CLEAN_LOG_FILES.items():
        if app_type not in _clean_handlers:
            # Create clean handler
            clean_handler = CleanLogHandler(clean_log_file)
            clean_handler.setLevel(logging.DEBUG)
            _clean_handlers[app_type] = clean_handler
            
            # Get the appropriate logger and add the clean handler
            if app_type == "system":
                logger_name = "huntarr"
            else:
                logger_name = app_type  # For app-specific loggers
            
            logger = get_logger(logger_name)
            logger.addHandler(clean_handler)


def get_clean_log_file(app_type: str) -> Optional[Path]:
    """
    Get the clean log file path for a specific app type.
    
    Args:
        app_type: The app type (e.g., 'sonarr', 'system')
        
    Returns:
        Path to the clean log file, or None if not found
    """
    return CLEAN_LOG_FILES.get(app_type)


def cleanup_clean_logs():
    """Remove all clean log handlers and close files."""
    from src.primary.utils.logger import get_logger
    
    for app_type, handler in _clean_handlers.items():
        if app_type == "system":
            logger_name = "huntarr"
        else:
            logger_name = app_type
            
        logger = get_logger(logger_name)
        logger.removeHandler(handler)
        handler.close()
    
    _clean_handlers.clear()
