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
    "readarr": LOG_DIR / "readarr.log" # Updated filename
}

# Global logger instances
logger = None
app_loggers: Dict[str, logging.Logger] = {}

def setup_logger(debug_mode=None, app_type=None):
    """Set up the logging configuration for the application
    
    Args:
        debug_mode: Whether to enable debug logging
        app_type: The type of application (sonarr, radarr, etc.)
        
    Returns:
        A configured Logger instance
    """
    global logger, app_loggers
    
    # Create a logger with the name "Huntarr" instead of including the edition
    app_logger = logging.getLogger("Huntarr")
    
    # Set debug mode from parameter or fallback to config
    if debug_mode is None:
        try:
            from primary import config
            debug_mode = getattr(config, "DEBUG_MODE", False)
        except ImportError:
            debug_mode = False
    
    # Get DEBUG_MODE from config, but only if we haven't been given a value
    # Use a safe approach to avoid circular imports
    use_debug_mode = False
    if debug_mode is None:
        try:
            # Try to get DEBUG_MODE from config, but don't fail if it's not available
            from primary.config import DEBUG_MODE as CONFIG_DEBUG_MODE
            use_debug_mode = CONFIG_DEBUG_MODE
        except (ImportError, AttributeError):
            # Default to False if there's any issue
            pass
    else:
        use_debug_mode = debug_mode
    
    # Determine the logger and log file to use
    if app_type in APP_LOG_FILES:
        # Use or create an app-specific logger
        log_name = f"huntarr.{app_type}"
        log_file = APP_LOG_FILES[app_type]
        
        if log_name in app_loggers:
            # Reset existing logger
            current_logger = app_loggers[log_name]
            for handler in current_logger.handlers[:]:
                current_logger.removeHandler(handler)
        else:
            # Create a new logger
            current_logger = logging.getLogger(log_name)
            app_loggers[log_name] = current_logger
    else:
        # Use or create the main logger
        log_name = "huntarr"
        log_file = MAIN_LOG_FILE
        
        if logger is None:
            # First-time setup
            current_logger = logging.getLogger(log_name)
            logger = current_logger
        else:
            # Reset handlers to avoid duplicates
            current_logger = logger
            for handler in current_logger.handlers[:]:
                current_logger.removeHandler(handler)
    
    # Set the log level based on use_debug_mode
    current_logger.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)
    
    # Create file handler for the web interface
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG if use_debug_mode else logging.INFO)
    
    # Set format - clearly indicate if this is a main log or app-specific log
    log_format = "%(asctime)s - "
    if app_type:
        # For app-specific logs, show clearly it's about interaction with that app
        log_format += f"huntarr-{app_type} - "
    else:
        # For main logger, just show it's Huntarr
        log_format += "huntarr - "
    log_format += "%(levelname)s - %(message)s"
    
    formatter = logging.Formatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    current_logger.addHandler(console_handler)
    current_logger.addHandler(file_handler)
    
    if use_debug_mode:
        current_logger.debug("Debug logging enabled")
    
    return current_logger

# Create the main logger instance on module import
logger = setup_logger()

def get_logger(app_type: str) -> logging.Logger:
    """
    Get a logger for a specific app type.
    
    Args:
        app_type: The app type to get a logger for.
        
    Returns:
        A logger specific to the app type.
    """
    # Check if we already have this logger configured
    log_name = f"huntarr.{app_type}"
    if log_name in app_loggers:
        return app_loggers[log_name]
    
    # If not, set up a new logger properly
    if app_type in APP_LOG_FILES:
        # Create the logger with the correct name
        app_logger = logging.getLogger(log_name)
        
        # Prevent propagation to avoid duplicate logs
        app_logger.propagate = False
        
        # Get debug mode setting
        try:
            from primary import config
            debug_mode = getattr(config, "DEBUG_MODE", False)
        except ImportError:
            debug_mode = False
            
        # Set appropriate log level
        app_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Create file handler
        log_file = APP_LOG_FILES[app_type]
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Set format for this app
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        app_logger.addHandler(console_handler)
        app_logger.addHandler(file_handler)
        
        # Store in our cache
        app_loggers[log_name] = app_logger
        return app_logger
    else:
        # Return the main logger if the app type is not recognized
        return logger

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