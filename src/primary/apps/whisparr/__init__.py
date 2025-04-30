"""
Whisparr app module for Huntarr
Contains functionality for missing items and quality upgrades in Whisparr

Supports both v2 (legacy) and v3 (Eros) API versions.
v2 - Original Whisparr API
v3 - Eros version of the Whisparr API
"""

# Module exports
from src.primary.apps.whisparr.missing import process_missing_items
from src.primary.apps.whisparr.upgrade import process_cutoff_upgrades
from src.primary.settings_manager import load_settings
from src.primary.utils.logger import get_logger

# Define logger for this module
whisparr_logger = get_logger("whisparr")

# For backward compatibility
process_missing_scenes = process_missing_items

def get_configured_instances():
    """Get all configured and enabled Whisparr instances"""
    settings = load_settings("whisparr")
    instances = []
    whisparr_logger.info(f"Loaded Whisparr settings for instance check: {settings}") 

    if not settings:
        whisparr_logger.debug("No settings found for Whisparr")
        return instances

    # Get the API version to use (v2 or v3/Eros)
    api_version = settings.get("whisparr_version", "v3")
    whisparr_logger.info(f"Using Whisparr API version: {api_version}")

    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        whisparr_logger.info(f"Found 'instances' list with {len(settings['instances'])} items. Processing...")
        for idx, instance in enumerate(settings["instances"]):
            whisparr_logger.debug(f"Checking instance #{idx}: {instance}")
            # Enhanced validation
            api_url = instance.get("api_url", "").strip()
            api_key = instance.get("api_key", "").strip()

            # Enhanced URL validation - ensure URL has proper scheme
            if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
                whisparr_logger.warning(f"Instance '{instance.get('name', 'Unnamed')}' has URL without http(s) scheme: {api_url}")
                api_url = f"http://{api_url}"
                whisparr_logger.warning(f"Auto-correcting URL to: {api_url}")

            is_enabled = instance.get("enabled", True)

            # Only include properly configured instances
            if is_enabled and api_url and api_key:
                # Return only essential instance details
                instance_data = {
                    "instance_name": instance.get("name", "Default"),
                    "api_url": api_url,
                    "api_key": api_key,
                    "api_version": api_version  # Add the API version to the instance data
                }
                instances.append(instance_data) 
                whisparr_logger.info(f"Added valid instance: {instance_data}") 
            elif not is_enabled:
                whisparr_logger.debug(f"Skipping disabled instance: {instance.get('name', 'Unnamed')}")
            else:
                # Log specifically why it's skipped (missing URL/Key but enabled)
                whisparr_logger.warning(f"Skipping instance '{instance.get('name', 'Unnamed')}' due to missing API URL or key (URL: '{api_url}', Key Set: {bool(api_key)}) ")
    else:
        whisparr_logger.info("No 'instances' list found or list is empty. Checking legacy config.")
        # Fallback to legacy single-instance config
        api_url = settings.get("api_url", "").strip()
        api_key = settings.get("api_key", "").strip()

        # Ensure URL has proper scheme
        if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
            whisparr_logger.warning(f"API URL missing http(s) scheme: {api_url}")
            api_url = f"http://{api_url}"
            whisparr_logger.warning(f"Auto-correcting URL to: {api_url}")

        if api_url and api_key:
            # Create a clean instance_data dict for the legacy instance
            instance_data = {
                "instance_name": "Default", 
                "api_url": api_url,
                "api_key": api_key,
                "api_version": api_version  # Add the API version to the instance data
            }
            instances.append(instance_data) 
            whisparr_logger.info(f"Added valid legacy instance: {instance_data}") 
        else:
            whisparr_logger.warning("No API URL or key found in legacy configuration")

    whisparr_logger.info(f"Returning {len(instances)} configured instances: {instances}") 
    return instances

__all__ = ["process_missing_items", "process_missing_scenes", "process_cutoff_upgrades", "get_configured_instances"]