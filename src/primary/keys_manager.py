#!/usr/bin/env python3
"""
Keys manager for Huntarr
Handles storage and retrieval of API keys and URLs from huntarr.json
"""

import os
import json
import pathlib
import logging
from typing import Dict, Any, Optional, Tuple

# Create a simple logger
logging.basicConfig(level=logging.INFO)
keys_logger = logging.getLogger("keys_manager")

# Use the centralized path configuration
from src.primary.utils.config_paths import CONFIG_PATH

# Settings directory using cross-platform configuration
SETTINGS_DIR = CONFIG_PATH
# Directory is already created by config_paths module

SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"

# Removed save_api_keys function

# Removed get_api_keys function

# Removed list_configured_apps function

# Keep other functions if they exist and are needed, otherwise the file might become empty.
# If this file solely managed API keys in the old way, it might be removable entirely,
# but let's keep it for now in case other key-related logic exists or is added later.