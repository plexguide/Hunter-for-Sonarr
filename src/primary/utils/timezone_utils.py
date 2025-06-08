#!/usr/bin/env python3
"""
Timezone utilities for Huntarr
Centralized timezone handling with proper fallbacks
"""

import os
import pytz
from typing import Union

# Cache for timezone to avoid repeated settings lookups
_timezone_cache = None
_cache_timestamp = 0
_cache_ttl = 5  # 5 seconds cache TTL


def clear_timezone_cache():
    """Clear the timezone cache to force a fresh lookup."""
    global _timezone_cache, _cache_timestamp
    _timezone_cache = None
    _cache_timestamp = 0


def get_user_timezone() -> pytz.BaseTzInfo:
    """
    Get the user's selected timezone with proper fallback handling.
    
    Fallback order:
    1. User's timezone setting from general settings
    2. TZ environment variable
    3. UTC as final fallback
    
    Returns:
        pytz.BaseTzInfo: The timezone object to use
    """
    global _timezone_cache, _cache_timestamp
    
    # Check cache first
    import time
    current_time = time.time()
    if _timezone_cache and (current_time - _cache_timestamp) < _cache_ttl:
        return _timezone_cache
    
    try:
        # First try to get timezone from user settings
        try:
            from src.primary import settings_manager
            general_settings = settings_manager.load_settings("general", use_cache=False)  # Force fresh read
            timezone_name = general_settings.get("timezone")
            
            if timezone_name and timezone_name != "UTC":
                try:
                    tz = pytz.timezone(timezone_name)
                    # Cache the result
                    _timezone_cache = tz
                    _cache_timestamp = current_time
                    return tz
                except pytz.UnknownTimeZoneError:
                    pass  # Fall through to TZ environment variable
        except Exception:
            pass  # Fall through to TZ environment variable
        
        # Second try TZ environment variable
        tz_env = os.environ.get('TZ')
        if tz_env:
            try:
                tz = pytz.timezone(tz_env)
                # Cache the result
                _timezone_cache = tz
                _cache_timestamp = current_time
                return tz
            except pytz.UnknownTimeZoneError:
                pass  # Fall through to UTC
        
        # Final fallback to UTC
        tz = pytz.UTC
        _timezone_cache = tz
        _cache_timestamp = current_time
        return tz
        
    except Exception:
        # If anything goes wrong, always return UTC
        tz = pytz.UTC
        _timezone_cache = tz
        _cache_timestamp = current_time
        return tz


def get_timezone_name() -> str:
    """
    Get the timezone name as a string.
    
    Returns:
        str: The timezone name (e.g., 'Pacific/Honolulu', 'UTC')
    """
    try:
        timezone = get_user_timezone()
        return str(timezone)
    except Exception:
        return "UTC" 