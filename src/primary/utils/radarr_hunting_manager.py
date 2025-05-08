import requests
from typing import Dict, Optional
from datetime import datetime
from .hunting_manager import HuntingManager

class RadarrHuntingManager:
    def __init__(self, hunting_manager: HuntingManager):
        self.hunting_manager = hunting_manager

    def check_movie_status(self, instance_name: str, api_key: str, base_url: str, 
                          movie_id: str, radarr_id: Optional[str] = None) -> Dict:
        """Check the status of a movie in Radarr."""
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

        # First check if the movie exists in Radarr
        if radarr_id:
            movie_url = f"{base_url}/api/v3/movie/{radarr_id}"
            try:
                response = requests.get(movie_url, headers=headers)
                if response.status_code == 200:
                    movie_data = response.json()
                    return self._process_movie_status(movie_data, instance_name, movie_id)
            except Exception as e:
                return {
                    "status": "Error",
                    "debug_info": {
                        "error": str(e),
                        "check_type": "movie_lookup",
                        "timestamp": datetime.now().isoformat()
                    }
                }

        # If no radarr_id or movie not found, check the queue
        queue_url = f"{base_url}/api/v3/queue"
        try:
            response = requests.get(queue_url, headers=headers)
            if response.status_code == 200:
                queue_data = response.json()
                return self._process_queue_status(queue_data, instance_name, movie_id)
        except Exception as e:
            return {
                "status": "Error",
                "debug_info": {
                    "error": str(e),
                    "check_type": "queue_lookup",
                    "timestamp": datetime.now().isoformat()
                }
            }

        return {
            "status": "Nothing Found",
            "debug_info": {
                "check_type": "no_results",
                "timestamp": datetime.now().isoformat()
            }
        }

    def _process_movie_status(self, movie_data: Dict, instance_name: str, 
                            movie_id: str) -> Dict:
        """Process the movie status from Radarr API response."""
        status = "Requested"
        debug_info = {
            "radarr_data": movie_data,
            "check_type": "movie_lookup",
            "timestamp": datetime.now().isoformat()
        }

        if movie_data.get("hasFile", False):
            status = "Found"
        elif movie_data.get("monitored", False):
            status = "Searching"

        self.hunting_manager.update_item_status(
            "radarr", instance_name, movie_id, status, debug_info
        )

        return {
            "status": status,
            "debug_info": debug_info
        }

    def _process_queue_status(self, queue_data: Dict, instance_name: str, 
                            movie_id: str) -> Dict:
        """Process the queue status from Radarr API response."""
        status = "Nothing Found"
        debug_info = {
            "radarr_data": queue_data,
            "check_type": "queue_lookup",
            "timestamp": datetime.now().isoformat()
        }

        for item in queue_data.get("records", []):
            if item.get("movieId") == movie_id:
                status = "Found"
                break

        self.hunting_manager.update_item_status(
            "radarr", instance_name, movie_id, status, debug_info
        )

        return {
            "status": status,
            "debug_info": debug_info
        } 