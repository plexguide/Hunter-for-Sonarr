#!/usr/bin/env python3
"""
Main entry point for Huntarr
"""

import sys
import os

# Add the current directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up the Python path to find modules
if os.path.exists('/app'):
    sys.path.insert(0, '/app')

# Now import the main function
from src.primary.main import main

if __name__ == "__main__":
    main()