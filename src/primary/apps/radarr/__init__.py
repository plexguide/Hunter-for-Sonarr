"""
Radarr app module for Huntarr
Contains functionality for missing movies and quality upgrades in Radarr
"""

# Module exports
from src.primary.apps.radarr.missing import process_missing_movies
from src.primary.apps.radarr.upgrade import process_cutoff_upgrades