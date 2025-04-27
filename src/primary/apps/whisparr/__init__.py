"""
Whisparr app module for Huntarr
Contains functionality for missing scenes and quality upgrades in Whisparr
"""

# Module exports
from src.primary.apps.whisparr.missing import process_missing_scenes
from src.primary.apps.whisparr.upgrade import process_cutoff_upgrades

__all__ = ["process_missing_scenes", "process_cutoff_upgrades"]