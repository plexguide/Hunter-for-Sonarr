#!/usr/bin/env python3
"""
Main entry point for Huntarr
"""

import sys
import os

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the main function from src.primary.main
from src.primary.main import start_huntarr

if __name__ == "__main__":
    start_huntarr()