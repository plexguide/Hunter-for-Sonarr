"""
Readarr module initialization
"""

from src.primary.apps.readarr.missing import process_missing_books
from src.primary.apps.readarr.upgrade import process_cutoff_upgrades

__all__ = ["process_missing_books", "process_cutoff_upgrades"]