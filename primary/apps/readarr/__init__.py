"""
Readarr module initialization
"""

from primary.apps.readarr.missing import process_missing_books
from primary.apps.readarr.upgrade import process_cutoff_upgrades

__all__ = ["process_missing_books", "process_cutoff_upgrades"]