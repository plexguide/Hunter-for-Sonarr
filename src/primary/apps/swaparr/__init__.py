"""
Swaparr app module for Huntarr
Contains functionality for handling stalled downloads in Starr apps
"""

# Add necessary imports for get_configured_instances
from src.primary.settings_manager import load_settings
from src.primary.utils.logger import get_logger

swaparr_logger = get_logger("swaparr")  # Get the logger instance

# We don't need the get_configured_instances function here anymore as it's defined in swaparr.py
# to avoid circular imports

# Export just the swaparr_logger for now
__all__ = ["swaparr_logger"]
