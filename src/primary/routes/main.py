from flask import Blueprint, request, jsonify
from src.primary.stats_manager import get_stats, reset_stats, load_hourly_caps, get_default_hourly_caps
from src.primary.settings_manager import get_general_settings
import logging
from flask_jwt_extended import jwt_required
from src.primary.auth_utils import admin_required

logger = logging.getLogger(__name__)

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def index():
    # Return the index page
    return "Huntarr API"

# Add new route for getting media statistics
@main_blueprint.route('/api/stats', methods=['GET'])
@jwt_required()
def api_get_stats():
    """Get media statistics for each app"""
    try:
        stats = get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error retrieving media statistics: {e}")
        return jsonify({
            "success": False,
            "message": "Error retrieving media statistics."
        }), 500

# Add route for resetting statistics
@main_blueprint.route('/api/stats/reset', methods=['POST'])
@jwt_required()
@admin_required
def api_reset_stats():
    """Reset media statistics"""
    try:
        app_type = None
        if request.is_json:
            app_type = request.json.get('app_type')
        
        reset_stats(app_type)
        return jsonify({
            "success": True,
            "message": f"Successfully reset statistics for {'all apps' if app_type is None else app_type}."
        })
    except Exception as e:
        logger.error(f"Error resetting media statistics: {e}")
        return jsonify({
            "success": False,
            "message": "Error resetting media statistics."
        }), 500

# Add route for getting hourly API caps
@main_blueprint.route('/api/hourly-caps', methods=['GET'])
@jwt_required()
def api_get_hourly_caps():
    """Get hourly API usage caps for each app"""
    try:
        # Load the current hourly caps
        caps = load_hourly_caps()
        
        # Get the hourly cap limit from general settings
        settings = get_general_settings()
        hourly_limit = settings.get('hourly_cap', 20)  # Default to 20 if not set
        
        return jsonify({
            "success": True,
            "caps": caps,
            "limit": hourly_limit
        })
    except Exception as e:
        logger.error(f"Error retrieving hourly API caps: {e}")
        return jsonify({
            "success": False,
            "message": "Error retrieving hourly API caps."
        }), 500