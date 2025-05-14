from src.primary.utils.logger import get_logger
from src.primary.settings_manager import load_settings

logger = get_logger("SSLSettings")

def get_ssl_verify() -> bool:
    """
    Returns the correct 'verify' value for requests to the API,
    based on the disable_ssl_verification setting.
    """
    try:
        settings = load_settings("general")
        disable_ssl = settings.get("disable_ssl_verification", False)
        logger.debug(f"SSL verification setting: {disable_ssl}")
        if disable_ssl is None:
            logger.warning("SSL verification setting not found, defaulting to secure.")
            return True  # Default to secure if not specified
        elif disable_ssl is True:
            logger.warning("SSL verification is DISABLED for API requests (self-signed certs allowed).")
        elif disable_ssl is False:
            logger.debug("SSL verification is ENABLED for API requests.")
        else:
            logger.error(f"Invalid value for disable_ssl_verification: {disable_ssl}. Defaulting to secure.")
            return True  # Default to secure if invalid value
        # If disable_ssl_verification is True, we disable SSL verification
        if disable_ssl:
            logger.warning("SSL verification is DISABLED for API requests (self-signed certs allowed).")
        return not disable_ssl
    except Exception as e:
        logger.error(f"Could not load settings for SSL verification: {e}")
        return True  # Default to secure
