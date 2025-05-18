"""
Route definitions for Swaparr API endpoints.
"""

from flask import Blueprint, request, jsonify
import os
import json
from src.primary.utils.logger import get_logger
from src.primary.settings_manager import load_settings, save_settings
from src.primary.apps.swaparr.handler import process_stalled_downloads
# Import centralized path configuration
from src.primary.utils.config_paths import CONFIG_PATH, SWAPARR_STATE_DIR

# Create the blueprint directly in this file
swaparr_bp = Blueprint('swaparr', __name__)
swaparr_logger = get_logger("swaparr")

@swaparr_bp.route('/status', methods=['GET'])
def get_status():
    """Get Swaparr status and statistics"""
    settings = load_settings("swaparr")
    enabled = settings.get("enabled", False)
    
    # Get strike statistics from all app state directories
    statistics = {}
    state_dir = SWAPARR_STATE_DIR
    
    if os.path.exists(state_dir):
        for app_name in os.listdir(state_dir):
            app_dir = os.path.join(state_dir, app_name)
            if os.path.isdir(app_dir):
                strike_file = os.path.join(app_dir, "strikes.json")
                if os.path.exists(strike_file):
                    try:
                        with open(strike_file, 'r') as f:
                            strike_data = json.load(f)
                            
                        total_items = len(strike_data)
                        removed_items = sum(1 for item in strike_data.values() if item.get("removed", False))
                        striked_items = sum(1 for item in strike_data.values() 
                                          if item.get("strikes", 0) > 0 and not item.get("removed", False))
                        
                        statistics[app_name] = {
                            "total_tracked": total_items,
                            "currently_striked": striked_items,
                            "removed": removed_items
                        }
                    except (json.JSONDecodeError, IOError) as e:
                        swaparr_logger.error(f"Error reading strike data for {app_name}: {str(e)}")
                        statistics[app_name] = {"error": str(e)}
    
    return jsonify({
        "enabled": enabled,
        "settings": {
            "max_strikes": settings.get("max_strikes", 3),
            "max_download_time": settings.get("max_download_time", "2h"),
            "ignore_above_size": settings.get("ignore_above_size", "25GB"),
            "remove_from_client": settings.get("remove_from_client", True),
            "dry_run": settings.get("dry_run", False)
        },
        "statistics": statistics
    })

@swaparr_bp.route('/settings', methods=['GET'])
def get_settings():
    """Get Swaparr settings"""
    settings = load_settings("swaparr")
    return jsonify(settings)

@swaparr_bp.route('/settings', methods=['POST'])
def update_settings():
    """Update Swaparr settings"""
    data = request.json
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    # Load current settings
    settings = load_settings("swaparr")
    
    # Update settings with provided data
    for key, value in data.items():
        settings[key] = value
    
    # Save updated settings
    success = save_settings("swaparr", settings)
    
    if success:
        return jsonify({"success": True, "message": "Settings updated successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to save settings"}), 500

@swaparr_bp.route('/reset', methods=['POST'])
def reset_strikes():
    """Reset all strikes for all apps or a specific app"""
    data = request.json
    app_name = data.get('app_name') if data else None
    
    state_dir = SWAPARR_STATE_DIR
    
    if not os.path.exists(state_dir):
        return jsonify({"success": True, "message": "No strike data to reset"})
    
    if app_name:
        # Reset strikes for a specific app
        app_dir = os.path.join(state_dir, app_name)
        if os.path.exists(app_dir):
            strike_file = os.path.join(app_dir, "strikes.json")
            if os.path.exists(strike_file):
                try:
                    os.remove(strike_file)
                    swaparr_logger.info(f"Reset strikes for {app_name}")
                    return jsonify({"success": True, "message": f"Strikes reset for {app_name}"})
                except IOError as e:
                    swaparr_logger.error(f"Error resetting strikes for {app_name}: {str(e)}")
                    return jsonify({"success": False, "message": f"Failed to reset strikes for {app_name}: {str(e)}"}), 500
        return jsonify({"success": False, "message": f"No strike data found for {app_name}"}), 404
    else:
        # Reset strikes for all apps
        try:
            for app_name in os.listdir(state_dir):
                app_dir = os.path.join(state_dir, app_name)
                if os.path.isdir(app_dir):
                    strike_file = os.path.join(app_dir, "strikes.json")
                    if os.path.exists(strike_file):
                        os.remove(strike_file)
            
            swaparr_logger.info("Reset all strikes")
            return jsonify({"success": True, "message": "All strikes reset"})
        except IOError as e:
            swaparr_logger.error(f"Error resetting all strikes: {str(e)}")
            return jsonify({"success": False, "message": f"Failed to reset all strikes: {str(e)}"}), 500

def register_routes(app):
    """Register Swaparr routes with the Flask app."""
    app.register_blueprint(swaparr_bp, url_prefix='/api/swaparr')
