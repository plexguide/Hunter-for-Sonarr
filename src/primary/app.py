import logging
import json
import pathlib

class WebAddressFilter(logging.Filter):
    """Filter out web interface availability messages"""
    def filter(self, record):
        if "Web interface available at http://" in record.getMessage():
            return False
        return True

def configure_logging():
    logging.basicConfig(level=logging.INFO)
    
    # Add filter to remove web interface URL logs
    for handler in logging.root.handlers:
        handler.addFilter(WebAddressFilter())
    
    logging.info("Logging is configured.")

def migrate_settings():
    """Migrate settings from nested to flat structure"""
    # Settings file path
    SETTINGS_DIR = pathlib.Path("/config")
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