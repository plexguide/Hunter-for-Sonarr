#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a consolidated list of app instances for the scheduler
This script scans all app configuration files and generates a unified list.json
for use by the scheduling UI
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger("huntarr.instance_list_generator")

def capitalize_first(string):
    """Capitalize the first letter of a string"""
    if not string:
        return ''
    return string[0].upper() + string[1:]

def generate_instance_list():
    """
    Scan all app configuration files and generate a list.json file
    containing all app instances for use by the scheduler
    """
    logger.debug("Generating app instance list for scheduler")
    
    # Define the app types we support
    app_types = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'bazarr']
    instances = {}
    
    # Initialize all app types with empty arrays
    for app_type in app_types:
        instances[app_type] = []
    
    # Base config directory (internal Docker path)
    config_dir = Path("/config")
    
    # Ensure the scheduling directory exists
    scheduling_dir = config_dir / "scheduling"
    os.makedirs(scheduling_dir, exist_ok=True)
    
    # Also save to a web-accessible location
    web_accessible_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "frontend" / "static" / "data"
    os.makedirs(web_accessible_dir, exist_ok=True)
    logger.debug(f"Web accessible directory: {web_accessible_dir}")
    
    # Scan each app's config file
    for app_type in app_types:
        config_file = config_dir / f"{app_type}.json"
        
        if not config_file.exists():
            logger.debug(f"No config file found for {app_type}, skipping")
            continue
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Check if we have an instances array in the config
            if config and "instances" in config and isinstance(config["instances"], list):
                # Add each instance to our instances object
                for index, instance in enumerate(config["instances"]):
                    instance_name = instance.get("name") or f"{capitalize_first(app_type)} Instance {index + 1}"
                    instances[app_type].append({
                        "id": str(index),
                        "name": instance_name
                    })
                logger.debug(f"Added {len(instances[app_type])} {app_type} instances")
            else:
                logger.debug(f"No instances found in {app_type}.json, adding default")
                # Add a default instance if none found
                instances[app_type] = [
                    {"id": "0", "name": f"{capitalize_first(app_type)} Default"}
                ]
        except Exception as e:
            logger.error(f"Error processing {app_type}.json: {str(e)}")
            # Add a default instance on error
            instances[app_type] = [
                {"id": "0", "name": f"{capitalize_first(app_type)} Default"}
            ]
    
    # Write the consolidated list to list.json in Docker config volume
    list_file = scheduling_dir / "list.json"
    with open(list_file, 'w') as f:
        json.dump(instances, f, indent=2)
    
    # Also write to web-accessible location
    web_list_file = web_accessible_dir / "app_instances.json"
    with open(web_list_file, 'w') as f:
        json.dump(instances, f, indent=2)
    
    logger.debug(f"Instance list generated successfully at {list_file} and {web_list_file}")
    return instances
