"""
Lidarr app module for Huntarr
Contains functionality for missing albums and quality upgrades in Lidarr
"""

# Module exports
from src.primary.apps.lidarr.missing import process_missing_albums
from src.primary.apps.lidarr.upgrade import process_cutoff_upgrades
from src.primary.settings_manager import load_settings
from src.primary.utils.logger import get_logger

# Define logger for this module
lidarr_logger = get_logger("lidarr")

def get_configured_instances():
    """Get all configured and enabled Lidarr instances"""
    settings = load_settings("lidarr")
    instances = []
    # lidarr_logger.info(f"Loaded Lidarr settings for instance check: {settings}") # Removed verbose log

    if not settings:
        lidarr_logger.debug("No settings found for Lidarr")
        return instances

    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        # lidarr_logger.info(f"Found 'instances' list with {len(settings['instances'])} items. Processing...") # Removed verbose log
        for idx, instance in enumerate(settings["instances"]):
            lidarr_logger.debug(f"Checking instance #{idx}: {instance}")
            # Enhanced validation
            api_url = instance.get("api_url", "").strip()
            api_key = instance.get("api_key", "").strip()

            # Enhanced URL validation - ensure URL has proper scheme
            if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
                lidarr_logger.warning(f"Instance '{instance.get('name', 'Unnamed')}' has URL without http(s) scheme: {api_url}")
                api_url = f"http://{api_url}"
                lidarr_logger.warning(f"Auto-correcting URL to: {api_url}")

            is_enabled = instance.get("enabled", True)

            # Only include properly configured instances
            if is_enabled and api_url and api_key:
                # Return only essential instance details
                instance_data = {
                    "instance_name": instance.get("name", "Default"),
                    "api_url": api_url,
                    "api_key": api_key,
                }
                instances.append(instance_data)
                # lidarr_logger.info(f"Added valid instance: {instance_data}") # Removed verbose log
            elif not is_enabled:
                lidarr_logger.debug(f"Skipping disabled instance: {instance.get('name', 'Unnamed')}")
            else:
                # Log specifically why it's skipped (missing URL/Key but enabled)
                lidarr_logger.warning(f"Skipping instance '{instance.get('name', 'Unnamed')}' due to missing API URL or key (URL: '{api_url}', Key Set: {bool(api_key)}) ")
    else:
        # lidarr_logger.info("No 'instances' list found or list is empty. Checking legacy config.") # Removed verbose log
        # Fallback to legacy single-instance config
        api_url = settings.get("api_url", "").strip()
        api_key = settings.get("api_key", "").strip()

        # Ensure URL has proper scheme
        if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
            lidarr_logger.warning(f"API URL missing http(s) scheme: {api_url}")
            api_url = f"http://{api_url}"
            lidarr_logger.warning(f"Auto-correcting URL to: {api_url}")

        if api_url and api_key:
            # Create a clean instance_data dict for the legacy instance
            instance_data = {
                "instance_name": "Default",
                "api_url": api_url,
                "api_key": api_key,
            }
            instances.append(instance_data)
            # lidarr_logger.info(f"Added valid legacy instance: {instance_data}") # Removed verbose log
        else:
            lidarr_logger.warning("No API URL or key found in legacy configuration")

    lidarr_logger.info(f"Found {len(instances)} configured and enabled Lidarr instances") # Changed log message
    return instances

__all__ = ["process_missing_albums", "process_cutoff_upgrades", "get_configured_instances"]