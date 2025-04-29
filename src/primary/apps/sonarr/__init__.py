"""
Sonarr module initialization
"""

# Use src.primary imports
from src.primary.apps.sonarr.missing import process_missing_episodes
from src.primary.apps.sonarr.upgrade import process_cutoff_upgrades
from src.primary.settings_manager import load_settings
from src.primary.utils.logger import get_logger

# Define logger for this module
sonarr_logger = get_logger("sonarr")

def get_configured_instances():
    """Get all configured and enabled Sonarr instances"""
    settings = load_settings("sonarr")
    instances = []
    # sonarr_logger.info(f"Loaded Sonarr settings for instance check: {settings}") # Removed verbose log

    if not settings:
        sonarr_logger.debug("No settings found for Sonarr")
        return instances

    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        # sonarr_logger.info(f"Found 'instances' list with {len(settings['instances'])} items. Processing...") # Removed verbose log
        for idx, instance in enumerate(settings["instances"]):
            sonarr_logger.debug(f"Checking instance #{idx}: {instance}")
            # Enhanced validation
            api_url = instance.get("api_url", "").strip()
            api_key = instance.get("api_key", "").strip()

            # Enhanced URL validation - ensure URL has proper scheme
            if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
                sonarr_logger.warning(f"Instance '{instance.get('name', 'Unnamed')}' has URL without http(s) scheme: {api_url}")
                api_url = f"http://{api_url}"
                sonarr_logger.warning(f"Auto-correcting URL to: {api_url}")

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
                # sonarr_logger.info(f"Added valid instance: {instance_data}") # Removed verbose log
            elif not is_enabled:
                sonarr_logger.debug(f"Skipping disabled instance: {instance.get('name', 'Unnamed')}")
            else:
                # Log specifically why it's skipped (missing URL/Key but enabled)
                sonarr_logger.warning(f"Skipping instance '{instance.get('name', 'Unnamed')}' due to missing API URL or key (URL: '{api_url}', Key Set: {bool(api_key)})")
    else:
        # sonarr_logger.info("No 'instances' list found or list is empty. Checking legacy config.") # Removed verbose log
        # Fallback to legacy single-instance config
        api_url = settings.get("api_url", "").strip()
        api_key = settings.get("api_key", "").strip()

        # Ensure URL has proper scheme
        if api_url and not (api_url.startswith('http://') or api_url.startswith('https://')):
            sonarr_logger.warning(f"API URL missing http(s) scheme: {api_url}")
            api_url = f"http://{api_url}"
            sonarr_logger.warning(f"Auto-correcting URL to: {api_url}")

        if api_url and api_key:
            # Create a clean instance_data dict for the legacy instance
            instance_data = {
                "instance_name": "Default",
                "api_url": api_url,
                "api_key": api_key,
            }
            instances.append(instance_data)
            # sonarr_logger.info(f"Added valid legacy instance: {instance_data}") # Removed verbose log
        else:
            sonarr_logger.warning("No API URL or key found in legacy configuration")

    sonarr_logger.info(f"Found {len(instances)} configured and enabled Sonarr instances") # Changed log message
    return instances

__all__ = ["process_missing_episodes", "process_cutoff_upgrades", "get_configured_instances"]