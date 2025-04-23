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

# Settings directory - Changed to match the updated settings_manager.py
SETTINGS_DIR = pathlib.Path("/config")
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"

# Removed save_api_keys function

# Removed get_api_keys function

# Removed list_configured_apps function

# Keep other functions if they exist and are needed, otherwise the file might become empty.
# If this file solely managed API keys in the old way, it might be removable entirely,
# but let's keep it for now in case other key-related logic exists or is added later.