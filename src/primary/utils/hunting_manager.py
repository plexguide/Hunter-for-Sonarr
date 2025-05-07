import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class HuntingManager:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.hunting_dir = os.path.join(config_dir, "hunting")
        self.time_config_path = os.path.join(self.hunting_dir, "time.json")
        self._ensure_directories()
        self._load_time_config()

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        os.makedirs(self.hunting_dir, exist_ok=True)
        os.makedirs(os.path.join(self.hunting_dir, "radarr"), exist_ok=True)

    def _load_time_config(self):
        """Load or create the time configuration."""
        if not os.path.exists(self.time_config_path):
            default_config = {
                "follow_up_time": 60,
                "max_time": 1440,
                "min_time": 5
            }
            with open(self.time_config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.time_config = default_config
        else:
            with open(self.time_config_path, 'r') as f:
                self.time_config = json.load(f)

    def update_time_config(self, follow_up_time: int):
        """Update the follow-up time configuration."""
        if not (self.time_config["min_time"] <= follow_up_time <= self.time_config["max_time"]):
            raise ValueError(f"Follow-up time must be between {self.time_config['min_time']} and {self.time_config['max_time']} minutes")
        
        self.time_config["follow_up_time"] = follow_up_time
        with open(self.time_config_path, 'w') as f:
            json.dump(self.time_config, f, indent=2)

    def get_instance_path(self, app_name: str, instance_name: str) -> str:
        """Get the path for an instance's tracking file."""
        return os.path.join(self.hunting_dir, app_name.lower(), f"{instance_name}.json")

    def add_tracking_item(self, app_name: str, instance_name: str, item_id: str, 
                         name: str, radarr_id: Optional[str] = None):
        """Add a new item to track."""
        instance_path = self.get_instance_path(app_name, instance_name)
        
        # Load or create instance tracking file
        if os.path.exists(instance_path):
            with open(instance_path, 'r') as f:
                tracking_data = json.load(f)
        else:
            tracking_data = {"tracking": {"items": []}}

        # Add new item
        new_item = {
            "id": item_id,
            "name": name,
            "status": "Requested",
            "requested_at": datetime.now().isoformat(),
            "last_checked": datetime.now().isoformat(),
            "radarr_id": radarr_id,
            "debug_info": {
                "added_by": "hunting_manager",
                "version": "1.0",
                "last_status_change": datetime.now().isoformat()
            }
        }
        
        tracking_data["tracking"]["items"].append(new_item)
        
        # Save updated tracking data
        with open(instance_path, 'w') as f:
            json.dump(tracking_data, f, indent=2)

    def update_item_status(self, app_name: str, instance_name: str, item_id: str, 
                          new_status: str, debug_info: Optional[Dict] = None):
        """Update the status of a tracked item."""
        instance_path = self.get_instance_path(app_name, instance_name)
        
        if not os.path.exists(instance_path):
            return False

        with open(instance_path, 'r') as f:
            tracking_data = json.load(f)

        for item in tracking_data["tracking"]["items"]:
            if item["id"] == item_id:
                item["status"] = new_status
                item["last_checked"] = datetime.now().isoformat()
                if debug_info:
                    item["debug_info"].update(debug_info)
                item["debug_info"]["last_status_change"] = datetime.now().isoformat()
                
                with open(instance_path, 'w') as f:
                    json.dump(tracking_data, f, indent=2)
                return True
        
        return False

    def get_latest_statuses(self, limit: int = 5) -> List[Dict]:
        """Get the latest hunt statuses across all apps and instances."""
        latest_statuses = []
        
        # Walk through all app directories
        for app_name in os.listdir(self.hunting_dir):
            app_path = os.path.join(self.hunting_dir, app_name)
            if not os.path.isdir(app_path) or app_name == "radarr":
                continue
                
            # Check each instance file
            for instance_file in os.listdir(app_path):
                if not instance_file.endswith('.json'):
                    continue
                    
                instance_path = os.path.join(app_path, instance_file)
                with open(instance_path, 'r') as f:
                    tracking_data = json.load(f)
                
                # Add all items from this instance
                for item in tracking_data["tracking"]["items"]:
                    latest_statuses.append({
                        "app_name": app_name,
                        "instance_name": instance_file[:-5],  # Remove .json
                        "media_name": item["name"],
                        "status": item["status"],
                        "id": item["id"],
                        "time_requested": item["requested_at"]
                    })
        
        # Sort by requested_at and get latest
        latest_statuses.sort(key=lambda x: x["time_requested"], reverse=True)
        return latest_statuses[:limit]

    def cleanup_old_records(self):
        """Clean up records that have exceeded their time limit."""
        cleanup_time = timedelta(minutes=self.time_config["follow_up_time"] + 10)
        
        for app_name in os.listdir(self.hunting_dir):
            app_path = os.path.join(self.hunting_dir, app_name)
            if not os.path.isdir(app_path):
                continue
                
            for instance_file in os.listdir(app_path):
                if not instance_file.endswith('.json'):
                    continue
                    
                instance_path = os.path.join(app_path, instance_file)
                with open(instance_path, 'r') as f:
                    tracking_data = json.load(f)
                
                # Filter out old items
                current_time = datetime.now()
                tracking_data["tracking"]["items"] = [
                    item for item in tracking_data["tracking"]["items"]
                    if (current_time - datetime.fromisoformat(item["requested_at"])) <= cleanup_time
                ]
                
                # Save updated tracking data
                with open(instance_path, 'w') as f:
                    json.dump(tracking_data, f, indent=2) 