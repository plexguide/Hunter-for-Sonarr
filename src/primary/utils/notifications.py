#!/usr/bin/env python3
"""
Notifications module for Huntarr
Handles sending notifications via Apprise
"""

import logging
import json
from typing import Optional, Dict, Any, Union

try:
    import apprise
except ImportError:
    apprise = None
    logging.warning("Apprise module not available. Notifications will be disabled.")

from src.primary.settings_manager import get_setting, load_settings

# Create a logger for notifications
logging.basicConfig(level=logging.INFO)
notifications_logger = logging.getLogger("huntarr_notifications")

# Notification levels
NOTIFICATION_LEVELS = {
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
    "critical": 50
}

# Cache for the Apprise instance
_apprise_instance = None
_last_apprise_url = None

def get_apprise_instance() -> Optional['apprise.Apprise']:
    """
    Get or create an Apprise instance with the configured URL
    
    Returns:
        Apprise instance or None if not configured or available
    """
    global _apprise_instance, _last_apprise_url
    
    if apprise is None:
        notifications_logger.warning("Apprise module not available. Notifications will be disabled.")
        return None
    
    # Load settings to get the Apprise URL
    general_settings = load_settings('general')
    apprise_url = general_settings.get('apprise_url', '')
    
    # Check if notifications are enabled
    if not general_settings.get('enable_notifications', False):
        notifications_logger.debug("Notifications are disabled in settings")
        return None
    
    # If URL is empty, notifications are not configured
    if not apprise_url:
        notifications_logger.debug("No Apprise URL configured")
        return None
    
    # Check if we need to create a new instance (first time or URL changed)
    if _apprise_instance is None or apprise_url != _last_apprise_url:
        try:
            notifications_logger.debug(f"Creating new Apprise instance with URL: {apprise_url}")
            _apprise_instance = apprise.Apprise()
            _apprise_instance.add(apprise_url)
            _last_apprise_url = apprise_url
        except Exception as e:
            notifications_logger.error(f"Error creating Apprise instance: {e}")
            _apprise_instance = None
    
    return _apprise_instance

def send_notification(
    title: str,
    message: str, 
    level: str = "info",
    tags: Optional[Union[str, list]] = None
) -> bool:
    """
    Send a notification using Apprise
    
    Args:
        title: Notification title
        message: Notification message body
        level: Notification level (debug, info, warning, error, critical)
        tags: Optional tags for notification filtering
        
    Returns:
        bool: Whether the notification was successfully sent
    """
    # Check if message level meets the configured minimum level
    general_settings = load_settings('general')
    configured_level = general_settings.get('notification_level', 'info')
    
    if NOTIFICATION_LEVELS.get(level, 0) < NOTIFICATION_LEVELS.get(configured_level, 0):
        notifications_logger.debug(
            f"Skipping notification: level '{level}' is below configured level '{configured_level}'"
        )
        return False
    
    apprise_instance = get_apprise_instance()
    if not apprise_instance:
        return False
    
    # Convert notify_type to Apprise notification type
    notify_type = {
        "debug": apprise.NotifyType.INFO,
        "info": apprise.NotifyType.INFO,
        "warning": apprise.NotifyType.WARNING,
        "error": apprise.NotifyType.FAILURE,
        "critical": apprise.NotifyType.FAILURE
    }.get(level, apprise.NotifyType.INFO)
    
    try:
        # Convert tag list to comma-separated string if it's a list
        if isinstance(tags, list):
            tags = ','.join(tags)
            
        result = apprise_instance.notify(
            body=message,
            title=title,
            notify_type=notify_type,
            tag=tags
        )
        
        if result:
            notifications_logger.debug(f"Notification sent: {title}")
        else:
            notifications_logger.error(f"Failed to send notification: {title}")
        
        return result
    except Exception as e:
        notifications_logger.error(f"Error sending notification: {e}")
        return False

def test_notification() -> Dict[str, Any]:
    """
    Send a test notification
    
    Returns:
        Dict with success status and message
    """
    try:
        result = send_notification(
            title="Huntarr Notification Test",
            message="This is a test notification from Huntarr.",
            level="info"
        )
        
        if result:
            return {
                "success": True,
                "message": "Test notification sent successfully."
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test notification. Check your Apprise URL configuration."
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending test notification: {str(e)}"
        }