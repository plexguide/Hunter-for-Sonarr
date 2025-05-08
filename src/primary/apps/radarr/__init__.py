"""
Radarr app module for Huntarr
Contains functionality for missing movies and quality upgrades in Radarr
"""

# Module exports
from src.primary.apps.radarr.missing import process_missing_movies
from src.primary.apps.radarr.upgrade import process_cutoff_upgrades

# Add necessary imports for get_configured_instances
from src.primary.settings_manager import load_settings
from src.primary.utils.logger import get_logger

radarr_logger = get_logger("radarr") # Get the logger instance

def get_configured_instances():
    """Get all configured and enabled Radarr instances"""
    settings = load_settings("radarr")
    instances = []
    
    if not settings:
        radarr_logger.debug("No settings found for Radarr")
        return instances
        
    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        for instance in settings["instances"]:
            if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                # Create a settings object for this instance by combining global settings with instance-specific ones
                instance_settings = settings.copy()
                # Remove instances list to avoid confusion
                if "instances" in instance_settings:
                    del instance_settings["instances"]
                
                # Override with instance-specific connection settings
                instance_settings["api_url"] = instance.get("api_url")
                instance_settings["api_key"] = instance.get("api_key")
                instance_settings["instance_name"] = instance.get("name", "Default")
                
                instances.append(instance_settings)
    else:
        # Fallback to legacy single-instance config
        api_url = settings.get("api_url")
        api_key = settings.get("api_key")
        if api_url and api_key:
            settings["instance_name"] = "Default"
            instances.append(settings)
    
    # Use debug level to avoid spamming logs, especially with 0 instances
    radarr_logger.debug(f"Found {len(instances)} configured and enabled Radarr instances")
    return instances

__all__ = ["process_missing_movies", "process_cutoff_upgrades", "get_configured_instances"]