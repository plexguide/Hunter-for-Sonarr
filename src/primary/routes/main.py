from flask import Blueprint, request, jsonify
from src.primary.stats_manager import get_stats, reset_stats

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def index():
    # ...existing code...
    
    # Remove or comment out any logging of the web interface URL here
    # logger.info(f"Web interface available at http://{request.host}")
    
    # ...existing code...

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