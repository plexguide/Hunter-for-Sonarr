"""
Lidarr app module for Huntarr
Contains functionality for missing albums and quality upgrades in Lidarr
"""

# Module exports
from src.primary.apps.lidarr.missing import process_missing_albums
from src.primary.apps.lidarr.upgrade import process_cutoff_upgrades

__all__ = ["process_missing_albums", "process_cutoff_upgrades"]