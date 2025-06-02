import logging
import json
import pathlib
from datetime import datetime
import time

class WebAddressFilter(logging.Filter):
    """Filter out web interface availability messages"""
    def filter(self, record):
        if "Web interface available at http://" in record.getMessage():
            return False
        return True

def configure_logging():
    # Get timezone set in the environment (this will be updated when user changes the timezone in UI)
    try:
        # Create a custom formatter that includes timezone information
        class TimezoneFormatter(logging.Formatter):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.converter = time.localtime  # Use local time instead of UTC
                
            def formatTime(self, record, datefmt=None):
                ct = self.converter(record.created)
                if datefmt:
                    return time.strftime(datefmt, ct)
                else:
                    # Use local time without timezone suffix for consistency
                    return time.strftime("%Y-%m-%d %H:%M:%S", ct)
        
        # Configure the formatter for all handlers
        formatter = TimezoneFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Reset the root logger and reconfigure with proper timezone handling
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(level=logging.INFO)
        
        # Apply the formatter to all handlers
        for handler in logging.root.handlers:
            handler.setFormatter(formatter)
            
    except Exception as e:
        # Fallback to basic logging if any issues
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.error(f"Error setting up timezone-aware logging: {e}")
    
    # Add filter to remove web interface URL logs
    for handler in logging.root.handlers:
        handler.addFilter(WebAddressFilter())
    
    logging.info("Logging is configured.")

def migrate_settings():
    """Migrate settings from nested to flat structure"""
    # Settings file path
    # Use the centralized path configuration
    from src.primary.utils.config_paths import CONFIG_PATH
    SETTINGS_DIR = CONFIG_PATH
    SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"
    
    if not SETTINGS_FILE.exists():
        logging.info(f"Settings file {SETTINGS_FILE} does not exist, nothing to migrate.")
        return
    
    try:
        # Read current settings
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            settings = json.load(file)
            
        # Flag to track if changes were made
        changes_made = False
        
        # Check and migrate each app's settings
        for app in ["sonarr", "radarr", "lidarr", "readarr"]:
            if app in settings and "huntarr" in settings[app]:
                logging.info(f"Found nested huntarr section in {app}, migrating...")
                
                # Move all settings from app.huntarr to app level
                for key, value in settings[app]["huntarr"].items():
                    if key not in settings[app]:
                        settings[app][key] = value
                
                # Remove the huntarr section
                del settings[app]["huntarr"]
                changes_made = True
            
            # Check for advanced section
            if app in settings and "advanced" in settings[app]:
                logging.info(f"Found advanced section in {app}, migrating...")
                
                # Move all settings from app.advanced to app level
                for key, value in settings[app]["advanced"].items():
                    if key not in settings[app]:
                        settings[app][key] = value
                
                # Remove the advanced section
                del settings[app]["advanced"]
                changes_made = True
        
        # Remove global section if present
        if "global" in settings:
            logging.info("Removing global section...")
            del settings["global"]
            changes_made = True
            
        # Remove UI section if present
        if "ui" in settings:
            logging.info("Removing UI section...")
            del settings["ui"]
            changes_made = True
        
        # Save changes if needed
        if changes_made:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=2)
            logging.info("Settings migration completed successfully.")
        else:
            logging.info("No changes needed, settings are already in the correct format.")
    
    except Exception as e:
        logging.error(f"Error migrating settings: {e}")

if __name__ == "__main__":
    configure_logging()
    logging.info("Starting Huntarr application")
    
    # Migrate settings to flat structure
    migrate_settings()
    
    # Using filtered logging
    logging.info("Web interface available at http://localhost:8080")
    logging.info("Application started")