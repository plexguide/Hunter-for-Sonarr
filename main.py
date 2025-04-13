#!/usr/bin/env python3
"""
Main entry point for Huntarr
This file simply imports from the src module and runs the appropriate entry point.
"""

import os
import sys

# Add the current directory to the path so the src module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main functionality from the src module
from src.primary.main import main

if __name__ == "__main__":
    # Run the main function
    main()