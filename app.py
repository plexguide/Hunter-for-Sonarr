#!/usr/bin/env python3
"""
Main entry point for the Huntarr application.
This file imports from the src folder.
"""

import os
import sys

# Add the current directory to the path so the src module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app from the src module
from src.app import app

if __name__ == '__main__':
    # Run the Flask application
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    host = '0.0.0.0'  # Listen on all interfaces
    port = int(os.environ.get('PORT', 9705))
    
    app.run(host=host, port=port, debug=debug_mode)