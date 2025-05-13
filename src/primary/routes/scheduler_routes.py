#!/usr/bin/env python3
"""
API routes for the Huntarr scheduler
Handles saving and loading schedule data
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify

# Set up logging
logger = logging.getLogger("huntarr.api.scheduler")

# Create blueprint
scheduler_blueprint = Blueprint('scheduler', __name__)

# Path to scheduler data
SCHEDULER_DIR = "/config/scheduler"
SCHEDULE_FILE = os.path.join(SCHEDULER_DIR, "schedule.json")

# Ensure scheduler directory exists
os.makedirs(SCHEDULER_DIR, exist_ok=True)


@scheduler_blueprint.route('/api/scheduler/load', methods=['GET'])
def load_schedules():
    """
    Load schedules from the schedule.json file
    Returns:
        JSON object containing the schedules organized by app type
    """
    try:
        logger.debug("Loading schedules from %s", SCHEDULE_FILE)
        
        # Create default schedule data if the file doesn't exist
        if not os.path.exists(SCHEDULE_FILE):
            logger.debug("Schedule file not found, creating empty default")
            default_data = {
                "global": [],
                "sonarr": [],
                "radarr": [],
                "readarr": [],
                "lidarr": [],
                "whisparr": [],
                "eros": []
            }
            # Create the file with default data
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump(default_data, f, indent=2)
            return jsonify(default_data)
        
        # Read the existing schedule file
        with open(SCHEDULE_FILE, 'r') as f:
            schedule_data = json.load(f)
            logger.debug("Loaded %s schedules", sum(len(schedules) for schedules in schedule_data.values()))
            return jsonify(schedule_data)
    
    except Exception as e:
        logger.error("Error loading schedules: %s", str(e))
        return jsonify({"error": str(e)}), 500


@scheduler_blueprint.route('/api/scheduler/save', methods=['POST'])
def save_schedules():
    """
    Save schedules to the schedule.json file
    Expects:
        JSON object containing the schedules organized by app type
    Returns:
        JSON confirmation
    """
    try:
        # Get the schedule data from the request
        schedule_data = request.json
        
        if not schedule_data or not isinstance(schedule_data, dict):
            return jsonify({"error": "Invalid schedule data"}), 400
        
        logger.debug("Saving %s schedules", sum(len(schedules) for schedules in schedule_data.values() if isinstance(schedules, list)))
        
        # Save to file
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        return jsonify({"status": "success", "message": "Schedules saved successfully"})
    
    except Exception as e:
        logger.error("Error saving schedules: %s", str(e))
        return jsonify({"error": str(e)}), 500
