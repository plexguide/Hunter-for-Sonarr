#!/usr/bin/env python3
"""
Script to generate a simplified main.py file for Windows builds.
This ensures Windows service support is properly included.
"""

import os
import sys

def generate_simplified_main():
    """Generate a simplified main.py file for Windows builds."""
    
    content = """#!/usr/bin/env python3
import os
import sys
import threading

# Ensure src is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Import the required modules
try:
    from primary.web_server import app
    from primary.background import start_huntarr, stop_event
    from primary.utils.logger import setup_main_logger
    
    # Windows service support
    if sys.platform == "win32" and len(sys.argv) > 1:
        if sys.argv[1] == "--install-service":
            from src.primary.windows_service import install_service
            sys.exit(0 if install_service() else 1)
        elif sys.argv[1] == "--remove-service":
            from src.primary.windows_service import remove_service
            sys.exit(0 if remove_service() else 1)
    
    def main():
        # Initialize main logger
        setup_main_logger()
        
        # Start background tasks in a thread
        background_thread = threading.Thread(target=start_huntarr, name="HuntarrBackground", daemon=True)
        background_thread.start()
        
        # Start the web server
        from waitress import serve
        serve(app, host="0.0.0.0", port=9705, threads=8)
    
    if __name__ == "__main__":
        main()
except Exception as e:
    print(f"Fatal error: {e}")
    sys.exit(1)
"""
    
    # Preserve original main.py if it exists
    if os.path.exists("main.py"):
        print("Backing up original main.py to main.py.orig")
        # Check if main.py.orig already exists, don't overwrite it
        if not os.path.exists("main.py.orig"):
            with open("main.py", "r") as f_in:
                with open("main.py.orig", "w") as f_out:
                    f_out.write(f_in.read())
    
    # Write the new main.py
    print("Writing simplified main.py with Windows service support")
    with open("main.py", "w") as f_out:
        f_out.write(content)
    
    print("Done!")

if __name__ == "__main__":
    generate_simplified_main()
