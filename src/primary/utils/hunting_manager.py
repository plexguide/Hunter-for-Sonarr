import json
import os
import time
import pathlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Create logger
logger = logging.getLogger("hunting_manager")

class HuntingManager:
    """The modernized HuntingManager that acts as a facade to the history and stateful management systems.
    
    This class no longer maintains its own state files or tracking directories.
    Instead, it dynamically pulls data from /config/history via the history_manager
    and integrates with the stateful_manager to check which IDs have been processed.
    
    The field_mapper.py handles the actual data processing and structure.
    """
    def __init__(self, config_dir: str):
        """Initialize the HuntingManager with minimal configuration.
        
        Args:
            config_dir: Base configuration directory (mostly for compatibility)
        """
        self.config_dir = config_dir
        self.history_dir = os.path.join(config_dir, "history")
        logger.info(f"HuntingManager initialized using history data from {self.history_dir}")

    def track_movie(self, item_id: str, instance_name: str, movie_info: Dict):
        """Track an item via the history manager.
        
        This is a no-op method since tracking is handled through history_manager
        and processed_ids through stateful_manager.
        
        Args:
            item_id: ID of the item to track
            instance_name: Name of the app instance
            movie_info: Dictionary of item information
        """
        # This is now a no-op method - all tracking is done via 
        # history_manager (create_history_entry) and stateful_manager (add_processed_id)
        pass

    def update_item_status(self, app_name: str, instance_name: str, item_id: str, 
                          new_status: str, debug_info: Optional[Dict] = None):
        """Update the status of a tracked item via history_manager.
        
        This is a no-op method since status updates are handled through
        the history_manager's update_history_entry_status method.
        
        Args:
            app_name: Type of app
            instance_name: Name of the app instance
            item_id: ID of the item
            new_status: New status value
            debug_info: Optional debug information
        """
        # This is now a no-op method - status updates are handled via 
        # history_manager (update_history_entry_status)
        pass

    def get_latest_statuses(self, limit: int = 5) -> List[Dict]:
        """Get the latest hunt statuses directly from history files.
        
        This now directly reads from the history directory to get the latest statuses.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of dictionaries with status information
        """
        # Import in method to avoid circular imports
        from src.primary.history_manager import get_history
        
        # Get history entries for all app types
        app_types = ['radarr', 'sonarr', 'lidarr', 'readarr', 'whisparr', 'eros']
        all_history = []
        
        for app_type in app_types:
            try:
                # Get most recent entries for this app type
                history = get_history(app_type, page=1, page_size=limit)
                if history and 'items' in history:
                    all_history.extend(history['items'])
            except Exception as e:
                print(f"Error getting history for {app_type}: {e}")
        
        # Sort by timestamp, most recent first
        all_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Format for the expected output format
        result = []
        for entry in all_history[:limit]:
            result.append({
                "app_type": entry.get("app_type", "unknown"),
                "instance": entry.get("instance_name", "unknown"),
                "id": entry.get("item_id", "unknown"),
                "name": entry.get("name", entry.get("title", "Unknown")),
                "status": entry.get("hunt_status", "Unknown"),
                "last_updated": entry.get("timestamp", ""),
                "requested_at": entry.get("timestamp", "")
            })
            
        return result

    def cleanup_old_records(self):
        """Cleanup is no longer needed as the history_manager handles record retention.
        
        This is maintained as a no-op method for compatibility.
        """
        # No longer needed - history retention is handled by history_manager
        pass