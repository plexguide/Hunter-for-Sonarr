#!/usr/bin/env python3
"""
Logging configuration for Huntarr
Supports separate log files for each application type
"""

import logging
import sys
import os
import pathlib
from typing import Dict, Optional

# Create log directory
LOG_DIR = pathlib.Path("/config/logs") # Changed path
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log file for general messages
MAIN_LOG_FILE = LOG_DIR / "huntarr.log"

# App-specific log files
APP_LOG_FILES = {
    "sonarr": LOG_DIR / "sonarr.log", # Updated filename
    "radarr": LOG_DIR / "radarr.log", # Updated filename
    "lidarr": LOG_DIR / "lidarr.log", # Updated filename
    "readarr": LOG_DIR / "readarr.log", # Updated filename
    "whisparr": LOG_DIR / "whisparr.log", # Added Whisparr
    "swaparr": LOG_DIR / "swaparr.log"  # Added Swaparr
}

# Global logger instances
logger: Optional[logging.Logger] = None
app_loggers: Dict[str, logging.Logger] = {}

def setup_main_logger(debug_mode=None):
    """Set up the main Huntarr logger."""
    global logger
    log_name = "huntarr"
    log_file = MAIN_LOG_FILE

    # Determine debug mode safely
    use_debug_mode = False
    if debug_mode is None:
        try:
            # Use a safe approach to avoid circular imports if possible
            from primary.config import DEBUG_MODE as CONFIG_DEBUG_MODE
            use_debug_mode = CONFIG_DEBUG_MODE
        except (ImportError, AttributeError):
            pass # Default to False
    else:
        use_debug_mode = debug_mode

    # Get or create the main logger instance
    current_logger = logging.getLogger(log_name)

    # Reset handlers each time setup is called to avoid duplicates
    # This is important if setup might be called again (e.g., config reload)
    for handler in current_logger.handlers[:]:
        current_logger.removeHandler(handler)

    current_logger.propagate = False # Prevent propagation to root logger
    current_logger.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)

    # Set format for the main logger
    log_format = "%(asctime)s - huntarr - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the main logger
    current_logger.addHandler(console_handler)
    current_logger.addHandler(file_handler)

    if use_debug_mode:
        current_logger.debug("Debug logging enabled for main logger")

    logger = current_logger # Assign to the global variable
    return current_logger

def get_logger(app_type: str) -> logging.Logger:
    """
    Get or create a logger for a specific app type.
    
    Args:
        app_type: The app type (e.g., 'sonarr', 'radarr').
        
    Returns:
        A logger specific to the app type, or the main logger if app_type is invalid.
    """
    if app_type not in APP_LOG_FILES:
        # Fallback to main logger if the app type is not recognized
        global logger
        if logger is None:
            # Ensure main logger is initialized if accessed before module-level setup
            setup_main_logger()
        # We checked logger is not None, so we can assert its type
        assert logger is not None
        return logger

    log_name = f"huntarr.{app_type}"
    if log_name in app_loggers:
        # Return cached logger instance
        return app_loggers[log_name]
    
    # If not cached, set up a new logger for this app type
    app_logger = logging.getLogger(log_name)
    
    # Prevent propagation to the main 'huntarr' logger or root logger
    app_logger.propagate = False
    
    # Determine debug mode setting safely
    try:
        from primary import config
        debug_mode = getattr(config, "DEBUG_MODE", False)
    except ImportError:
        debug_mode = False
            
    # Set appropriate log level
    app_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Reset handlers in case this logger existed before but wasn't cached
    # (e.g., across restarts without clearing logging._handlers)
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Create file handler for the specific app log file
    log_file = APP_LOG_FILES[app_type]
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Set a distinct format for this app log
    log_format = f"%(asctime)s - huntarr.{app_type} - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add the handlers specific to this app logger
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    
    # Cache the configured logger
    app_loggers[log_name] = app_logger

    if debug_mode:
        app_logger.debug(f"Debug logging enabled for {app_type} logger")
        
    return app_logger

def debug_log(message: str, data: object = None, app_type: Optional[str] = None) -> None:
    """
    Log debug messages with optional data.
    
    Args:
        message: The message to log.
        data: Optional data to include with the message.
        app_type: Optional app type to log to a specific app's log file.
    """
    current_logger = get_logger(app_type) if app_type else logger
    
    if current_logger.level <= logging.DEBUG:
        current_logger.debug(f"{message}")
        if data is not None:
            try:
                import json
                as_json = json.dumps(data)
                if len(as_json) > 500:
                    as_json = as_json[:500] + "..."
                current_logger.debug(as_json)
            except:
                data_str = str(data)
                if len(data_str) > 500:
                    data_str = data_str[:500] + "..."
                current_logger.debug(data_str)

# Initialize the main logger instance when the module is imported
logger = setup_main_logger()