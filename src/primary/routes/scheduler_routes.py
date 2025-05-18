#!/usr/bin/env python3
"""
Scheduler API Routes
Handles API endpoints for scheduler management
"""

import os
import json
import logging
from flask import Blueprint, jsonify, request, Response
from datetime import datetime

# Import the scheduler engine to get execution history
from src.primary.scheduler_engine import get_execution_history

# Create logger
scheduler_logger = logging.getLogger("scheduler")

# Create blueprint
scheduler_api = Blueprint('scheduler_api', __name__)

# Import instance list generator to access its functions
from src.primary.utils.instance_list_generator import generate_instance_list

# Configuration file path
# Use the centralized path configuration
from src.primary.utils.config_paths import SCHEDULER_DIR

# Convert Path object to string for compatibility with os.path functions
CONFIG_DIR = str(SCHEDULER_DIR)
SCHEDULE_FILE = os.path.join(CONFIG_DIR, "schedule.json")

def ensure_config_dir():
    """Ensure the config directory exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        scheduler_logger.info(f"Created config directory: {CONFIG_DIR}")

@scheduler_api.route('/api/scheduler/load', methods=['GET'])
def load_schedules():
    """Load schedules from the JSON file"""
    try:
        ensure_config_dir()
        
        # Default empty schedules
        schedules = {
            "global": [],
            "sonarr": [],
            "radarr": [],
            "lidarr": [],
            "readarr": []
        }
        
        # Load from file if it exists
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r') as f:
                loaded_data = json.load(f)
                if loaded_data and isinstance(loaded_data, dict):
                    # Update with data from file, keeping default structure
                    schedules.update(loaded_data)
            scheduler_logger.info(f"Loaded schedules from {SCHEDULE_FILE}")
        else:
            scheduler_logger.info(f"No schedule file found at {SCHEDULE_FILE}, returning empty schedules")
        
        # Add CORS headers
        response = Response(json.dumps(schedules))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        error_msg = f"Error loading schedules: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500
        

@scheduler_api.route('/api/scheduler/history', methods=['GET'])
def get_scheduler_history():
    """Return the execution history for the scheduler"""
    try:
        history = get_execution_history()
        response = Response(json.dumps({
            "success": True,
            "history": history,
            "timestamp": datetime.now().isoformat()
        }))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        error_msg = f"Error getting scheduler history: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@scheduler_api.route('/api/scheduling/list', methods=['GET'])
def get_scheduler_instance_list():
    """Return the list of app instances for the scheduler UI"""
    try:
        # Generate the instance list (this will create list.json in the scheduling directory)
        instances = generate_instance_list()
        
        # Return the generated data directly as JSON
        return jsonify(instances)
    except Exception as e:
        scheduler_logger.error(f"Error generating instance list: {str(e)}")
        return jsonify({
            'error': f"Failed to generate instance list: {str(e)}",
            'order': ['sonarr', 'radarr', 'readarr', 'lidarr', 'whisparr', 'eros']
        }), 500

@scheduler_api.route('/api/scheduler/save', methods=['POST'])
def save_schedules():
    """Save schedules to the JSON file"""
    try:
        ensure_config_dir()
        
        # Get schedule data from request
        schedules = request.json
        
        if not schedules or not isinstance(schedules, dict):
            return jsonify({"error": "Invalid schedule data format"}), 400
        
        # Save to file
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        
        scheduler_logger.info(f"Saved schedules to {SCHEDULE_FILE}")
        
        # Add timestamp to response
        response_data = {
            "success": True,
            "message": "Schedules saved successfully",
            "timestamp": datetime.now().isoformat(),
            "file": SCHEDULE_FILE
        }
        
        # Add CORS headers
        response = Response(json.dumps(response_data))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        error_msg = f"Error saving schedules: {str(e)}"
        scheduler_logger.error(error_msg)
        return jsonify({"error": error_msg}), 500
