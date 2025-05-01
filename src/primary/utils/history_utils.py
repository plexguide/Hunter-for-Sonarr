#!/usr/bin/env python3

from src.primary.history_manager import add_history_entry
from src.primary.utils.logger import get_logger

logger = get_logger("history")

def log_processed_media(app_type, media_name, media_id, instance_name):
    """
    Log when media is processed by an app instance
    
    Parameters:
    - app_type: str - The app type (sonarr, radarr, etc)
    - media_name: str - Name of the processed media
    - media_id: str/int - ID of the processed media
    - instance_name: str - Name of the instance that processed it
    
    Returns:
    - bool - Success or failure
    """
    try:
        entry_data = {
            "name": media_name,
            "id": str(media_id),
            "instance_name": instance_name
        }
        
        result = add_history_entry(app_type, entry_data)
        if result:
            logger.info(f"Logged history entry for {app_type}: {media_name}")
            return True
        else:
            logger.error(f"Failed to log history entry for {app_type}: {media_name}")
            return False
    except Exception as e:
        logger.error(f"Error logging history entry: {str(e)}")
        return False
