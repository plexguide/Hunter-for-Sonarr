"""
Unified Field Handler for Hunting Manager

This module defines the expected fields for each app type to be stored in history entries
and provides utilities for creating new entries, updating entries, and extracting data.
It eliminates any translation layer by directly handling all field operations.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Tuple

logger = logging.getLogger(__name__)

# This structure defines what data is needed for each app type
# - Required: Fields that must be present in any history entry
# - API endpoints: What API calls are needed to get the data
# - API fields: The specific fields to take from each API call (directly as-is)
# - Queue check: How to match queue items to this content type
# - Display: How to format the display name for the entry
APP_CONFIG = {
    "radarr": {
        "required_fields": [
            "id", "title", "year", "monitored", "hasFile"
        ],
        "api_calls": {
            "primary": "get_movie_by_id",  # Required, called first to get basic info
            "file": {                     # Optional, called if primary indicates a file exists
                "endpoint": "get_movie_file",
                "condition": "hasFile",
                "condition_value": True,
                "id_source": "movieFile.id"
            },
            "queue": {                    # Always called once per batch to check queue status
                "endpoint": "get_download_queue",
                "match_field": "movieId"  # How to match queue items to this content type
            }
        },
        "api_fields": {
            "get_movie_by_id": [
                "id", "title", "year", "hasFile", "monitored", 
                "status", "path", "sortTitle", "overview", "images",
                "added", "movieFile", "imdbId", "tmdbId", "qualityProfileId"
            ],
            "get_movie_file": [
                "id", "size", "quality", "dateAdded", "mediaInfo", 
                "originalFilePath", "relativePath", "resolution"
            ],
            "get_download_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft"
            ]
        },
        "display_info": {
            "name_format": "{title} ({year})",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "sonarr": {
        "required_fields": [
            "id", "title", "monitored", "statistics"
        ],
        "api_calls": {
            "primary": "get_series_by_id",
            "episode": {               # Episode info is conditionally fetched for episode-based operations
                "endpoint": "get_episode",
                "multi_item": True,   # Multiple episodes per series
                "condition": None,     # Always fetch if episode IDs are available
                "id_source": "episodeIds" # List of IDs to fetch
            },
            "queue": {
                "endpoint": "get_queue",
                "match_field": "seriesId"
            }
        },
        "api_fields": {
            "get_series_by_id": [
                "id", "title", "monitored", "statistics", "status",
                "path", "overview", "images", "added", "seasonCount",
                "seasons", "tvdbId", "imdbId", "tvMazeId", "qualityProfileId"
            ],
            "get_episode": [
                "id", "seriesId", "seasonNumber", "episodeNumber", "title",
                "airDate", "airDateUtc", "hasFile", "monitored", "absoluteEpisodeNumber"
            ],
            "get_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft", "title", "episode"
            ]
        },
        "display_info": {
            "name_format": "{title}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "lidarr": {
        "required_fields": [
            "id", "artistName", "monitored", "statistics"
        ],
        "api_calls": {
            "primary": "get_artist_by_id",
            "album": {                # Album info is conditionally fetched
                "endpoint": "get_album_by_artist_id",
                "multi_item": True,  # Multiple albums per artist
                "condition": None,    # Always fetch
                "id_source": "id"    # Artist ID to fetch albums for
            },
            "queue": {
                "endpoint": "get_queue",
                "match_field": "artistId"
            }
        },
        "api_fields": {
            "get_artist_by_id": [
                "id", "artistName", "monitored", "statistics", "status",
                "path", "overview", "images", "added", "albumCount",
                "qualityProfileId", "metadataProfileId", "foreignArtistId"
            ],
            "get_album_by_artist_id": [
                "id", "title", "releaseDate", "albumType", "duration",
                "monitored", "trackCount", "media", "ratings", "disambiguation"
            ],
            "get_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft", "title", "album"
            ]
        },
        "display_info": {
            "name_format": "{artistName}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "readarr": {
        "required_fields": [
            "id", "authorName", "monitored", "statistics"
        ],
        "api_calls": {
            "primary": "get_author_by_id",
            "book": {                # Book info is conditionally fetched
                "endpoint": "get_books_by_author_id",
                "multi_item": True, # Multiple books per author
                "condition": None,   # Always fetch
                "id_source": "id"   # Author ID to fetch books for
            },
            "queue": {
                "endpoint": "get_queue",
                "match_field": "authorId"
            }
        },
        "api_fields": {
            "get_author_by_id": [
                "id", "authorName", "monitored", "statistics", "status",
                "path", "overview", "images", "added", "qualityProfileId",
                "metadataProfileId", "foreignAuthorId"
            ],
            "get_books_by_author_id": [
                "id", "title", "releaseDate", "pageCount", "overview",
                "monitored", "ratings", "editions", "seriesTitle"
            ],
            "get_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft", "title", "book"
            ]
        },
        "display_info": {
            "name_format": "{authorName}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "whisparr": {
        "required_fields": [
            "id", "title", "monitored", "hasFile"
        ],
        "api_calls": {
            "primary": "get_movie_by_id",
            "file": {
                "endpoint": "get_movie_file",
                "condition": "hasFile",
                "condition_value": True,
                "id_source": "movieFile.id"
            },
            "queue": {
                "endpoint": "get_download_queue",
                "match_field": "movieId"
            }
        },
        "api_fields": {
            "get_movie_by_id": [
                "id", "title", "hasFile", "monitored", "status",
                "path", "overview", "images", "added", "studio",
                "qualityProfileId", "imdbId"
                # Legacy Whisparr doesn't have these fields: genres, tags, collection
            ],
            "get_movie_file": [
                "id", "size", "quality", "dateAdded", "mediaInfo",
                "originalFilePath", "relativePath", "resolution"
            ],
            "get_download_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft"
            ]
        },
        "display_info": {
            "name_format": "{title}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "eros": {
        "required_fields": [
            "id", "title", "monitored", "hasFile"
        ],
        "api_calls": {
            "primary": "get_movie_by_id", # Future Whisparr V3 (Eros branch) API structure
            "file": {
                "endpoint": "get_movie_file",
                "condition": "hasFile",
                "condition_value": True,
                "id_source": "movieFile.id"
            },
            "queue": {
                "endpoint": "get_download_queue",
                "match_field": "movieId"
            }
        },
        "api_fields": {
            "get_movie_by_id": [
                "id", "title", "hasFile", "monitored", "status",
                "path", "overview", "images", "added", "studio",
                "qualityProfileId", "imdbId", "genres", "tags", "collection"
                # Eros has additional fields over legacy Whisparr: genres, tags, collection
            ],
            "get_movie_file": [
                "id", "size", "quality", "dateAdded", "mediaInfo",
                "originalFilePath", "relativePath", "resolution"
            ],
            "get_download_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft"
            ]
        },
        "display_info": {
            "name_format": "{title}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    },
    
    "whisparrv2": { # This is now using the Eros API exclusively
        "required_fields": [
            "id", "title", "monitored", "hasFile"
        ],
        "api_calls": {
            "primary": "get_movie_by_id",
            "file": {
                "endpoint": "get_movie_file",
                "condition": "hasFile",
                "condition_value": True,
                "id_source": "movieFile.id"
            },
            "queue": {
                "endpoint": "get_download_queue",
                "match_field": "movieId"
            }
        },
        "api_fields": {
            "get_movie_by_id": [
                "id", "title", "hasFile", "monitored", "status",
                "path", "overview", "images", "added", "studio",
                "qualityProfileId", "imdbId", "genres", "tags", "collection"
                # Now includes all Eros fields since it's using the Eros API exclusively
            ],
            "get_movie_file": [
                "id", "size", "quality", "dateAdded", "mediaInfo",
                "originalFilePath", "relativePath", "resolution"
            ],
            "get_download_queue": [
                "status", "progress", "protocol", "downloadId",
                "estimatedCompletionTime", "statusMessages", "errorMessage",
                "size", "sizeleft", "timeleft"
                # Added the size-related fields to match Eros configuration
            ]
        },
        "display_info": {
            "name_format": "{title}",
            "id_field": "id",
            "default_operation": "monitored"
        }
    }
}

def get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
    """
    Extract a value from a nested dictionary using dot notation.

    Examples:
        get_nested_value({"a": {"b": {"c": 1}}}, "a.b.c") -> 1
        get_nested_value({"a": [{"b": 1}, {"b": 2}]}, "a[0].b") -> 1

    Args:
        data: The dictionary to extract from
        field_path: The path to the field, using dot notation

    Returns:
        The extracted value, or None if not found
    """
    if not data or not field_path:
        return None

    # Handle special comparison operators for boolean conversion
    if " > " in field_path:
        field_part, value_part = field_path.split(" > ")
        try:
            actual_value = get_nested_value(data, field_part)
            threshold = int(value_part)
            return actual_value > threshold
        except (ValueError, TypeError):
            return None

    # Normal field navigation
    parts = field_path.split(".")
    current = data

    for part in parts:
        # Handle array indexing like "items[0]"
        if "[" in part and "]" in part:
            array_part = part.split("[")[0]
            index_part = part.split("[")[1].split("]")[0]

            # Get the array
            if array_part not in current:
                return None
            array_data = current[array_part]

            # Get indexed item
            try:
                index = int(index_part)
                if not isinstance(array_data, list) or index >= len(array_data):
                    return None
                current = array_data[index]
            except (ValueError, IndexError):
                return None
        else:
            # Regular dictionary access
            if part not in current:
                return None
            current = current[part]

    return current

def fetch_api_data_for_item(app_type: str, item_id: str, api_handlers: Dict[str, Callable]) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Fetch all necessary API data for an item using the app configuration.
    Centralizes API fetching based on the APP_CONFIG structure.
    
    Args:
        app_type: The type of app (radarr, sonarr, etc.)
        item_id: The ID of the item being tracked
        api_handlers: Dictionary of API handler functions (name -> function)
    
    Returns:
        Tuple of (primary_data, file_data, queue_items)
    """
    app_config = APP_CONFIG.get(app_type)
    if not app_config:
        logger.error(f"No configuration found for app type: {app_type}")
        return None, None, []
    
    # Get API call configurations
    api_calls = app_config.get("api_calls", {})
    
    # Fetch primary data
    primary_endpoint = api_calls.get("primary")
    if not primary_endpoint or primary_endpoint not in api_handlers:
        logger.error(f"Missing primary API endpoint for {app_type}")
        return None, None, []
    
    # Call the primary API to get basic item data
    try:
        primary_data = api_handlers[primary_endpoint](item_id)
        if not primary_data:
            logger.warning(f"No data returned from {primary_endpoint} for ID {item_id}")
            return None, None, []
    except Exception as e:
        logger.error(f"Error fetching primary data for {app_type} item {item_id}: {str(e)}")
        return None, None, []
    
    # Fetch file data if needed
    file_data = None
    file_config = api_calls.get("file")
    if file_config:
        condition_field = file_config.get("condition")
        condition_value = file_config.get("condition_value")
        
        # Check if condition is met to fetch file data
        if condition_field in primary_data and primary_data[condition_field] == condition_value:
            file_endpoint = file_config.get("endpoint")
            id_source = file_config.get("id_source")
            if file_endpoint and id_source and file_endpoint in api_handlers:
                # Get the file ID from the primary data
                file_id = get_nested_value(primary_data, id_source)
                if file_id:
                    try:
                        file_data = api_handlers[file_endpoint](file_id)
                    except Exception as e:
                        logger.warning(f"Error fetching file data: {str(e)}")
    
    # Queue data is handled separately and passed in from the caller
    
    return primary_data, file_data, []

def create_history_entry(app_type: str, instance_name: str, item_id: str, 
                       primary_data: Dict[str, Any], 
                       file_data: Optional[Dict[str, Any]] = None, 
                       queue_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Create a new history entry with fields from the API responses.
    This creates the exact JSON structure needed for the history manager.
    
    Args:
        app_type: The type of app (radarr, sonarr, etc.)
        instance_name: The name of the app instance
        item_id: The ID of the item being tracked
        primary_data: Primary API data for the item
        file_data: Optional file data if available
        queue_data: Optional queue data if available
    
    Returns:
        Dict containing the complete history entry
    """
    app_config = APP_CONFIG.get(app_type)
    if not app_config or not primary_data:
        logger.error(f"Cannot create history entry: missing config or data for {app_type}")
        return None
    
    # Create base entry with required metadata
    timestamp = int(time.time())
    entry = {
        # Standard history fields
        "date_time": timestamp,
        "date_time_readable": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        "id": str(item_id),
        "instance_name": instance_name,
        "app_type": app_type,
        "operation_type": app_config["display_info"].get("default_operation", "monitored"),
        "hunt_status": determine_hunt_status(app_type, primary_data, queue_data)
    }
    
    # Formatted name for display
    name_format = app_config["display_info"].get("name_format", "{id}")
    try:
        entry["processed_info"] = name_format.format(**primary_data)
    except (KeyError, ValueError):
        entry["processed_info"] = f"Item {item_id}"
    
    # Add primary API fields
    api_fields = app_config.get("api_fields", {})
    primary_endpoint = app_config["api_calls"].get("primary")
    if primary_endpoint and primary_endpoint in api_fields:
        for field in api_fields[primary_endpoint]:
            if field in primary_data:
                entry[field] = primary_data[field]
    
    # Add file data fields
    file_config = app_config["api_calls"].get("file")
    if file_config and file_data:
        file_endpoint = file_config.get("endpoint")
        if file_endpoint and file_endpoint in api_fields:
            for field in api_fields[file_endpoint]:
                if field in file_data:
                    entry[f"file_{field}"] = file_data[field]
    
    # Add queue data
    if queue_data:
        queue_config = app_config["api_calls"].get("queue")
        if queue_config:
            queue_endpoint = queue_config.get("endpoint")
            match_field = queue_config.get("match_field")
            
            # Find matching queue item
            for queue_item in queue_data:
                if queue_item.get(match_field) == int(item_id):
                    if queue_endpoint and queue_endpoint in api_fields:
                        for field in api_fields[queue_endpoint]:
                            if field in queue_item:
                                entry[f"queue_{field}"] = queue_item[field]
                    entry["in_queue"] = True
                    break
            else:
                entry["in_queue"] = False
    
    return entry

def determine_hunt_status(app_type: str, api_data: Dict[str, Any], queue_data: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Determine the hunt status based on API data and queue status.
    
    Args:
        app_type: The type of app (radarr, sonarr, etc.)
        api_data: Primary API data for the item
        queue_data: Optional queue data if available
        
    Returns:
        String status: "Downloaded", "Found", "Searching", or "Not Tracked"
    """
    # First check for missing data
    if not api_data:
        return "Not Tracked"
    
    # App-specific field checks for determining if item has a file
    has_file = False
    item_id = api_data.get('id')
    
    if app_type == "radarr" or app_type == "whisparr" or app_type == "eros":
        has_file = api_data.get('hasFile', False)
    elif app_type == "sonarr":
        has_file = api_data.get('statistics', {}).get('episodeFileCount', 0) > 0
    elif app_type == "lidarr":
        has_file = api_data.get('statistics', {}).get('trackFileCount', 0) > 0
    elif app_type == "readarr":
        has_file = api_data.get('statistics', {}).get('bookFileCount', 0) > 0
    
    # If item has a file, it's downloaded
    if has_file:
        return "Downloaded"
    
    # Check if item is in download queue
    in_queue = False
    if queue_data:
        # Each app type uses a different ID field in the queue
        id_field_map = {
            "radarr": "movieId", 
            "sonarr": "seriesId",
            "lidarr": "artistId", 
            "readarr": "authorId",
            "whisparr": "movieId",
            "eros": "movieId"
        }
        id_field = id_field_map.get(app_type, "id")
        
        for queue_item in queue_data:
            if queue_item.get(id_field) == item_id:
                in_queue = True
                break
    
    # If in queue but not downloaded, it's found
    if in_queue:
        return "Found"
    
    # If monitored but not in queue or downloaded, it's searching
    if api_data.get('monitored', False):
        return "Searching"
    
    # Default fallback
    return "Not Tracked"
