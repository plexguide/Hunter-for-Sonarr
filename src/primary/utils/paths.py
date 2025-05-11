import sys
import os
from appdirs import user_data_dir

APP_NAME = "Huntarr"
APP_AUTHOR = "Huntarr"


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # For one-folder builds, _MEIPASS is the path to the main executable's directory.
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_app_data_dir():
    """ 
    Returns the user-specific data directory for Huntarr.
    Ensures the directory exists.
    Example: 
        Windows: C:\Users\<User>\AppData\Local\Huntarr\Huntarr
        macOS: ~/Library/Application Support/Huntarr
        Linux: ~/.local/share/Huntarr or /var/opt/Huntarr or similar
    """
    # user_data_dir(appname, appauthor, version=None, roaming=False)
    # Using appname as APP_AUTHOR for simplicity here, adjust if Huntarr has a known author string
    app_data_path = user_data_dir(APP_NAME, APP_AUTHOR, roaming=False) 
    
    # Create the directory if it doesn't exist
    if not os.path.exists(app_data_path):
        os.makedirs(app_data_path)
        print(f"Created application data directory: {app_data_path}") # Log this or print for first run
    return app_data_path

if __name__ == '__main__':
    # For testing the functions
    print(f"Resource path for 'frontend/static': {resource_path('frontend/static')}")
    print(f"Application data directory: {get_app_data_dir()}")
