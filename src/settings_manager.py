#!/usr/bin/env python3
"""
Simplified settings manager that only uses environment variables
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("settings_manager")

def get_env_setting(key, default=None, convert_type=None):
    """Get a setting from environment variables"""
    value = os.environ.get(key, default)
    
    if convert_type:
        try:
            return convert_type(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert {key}={value} to {convert_type.__name__}, using default: {default}")
            return default
    
    return value