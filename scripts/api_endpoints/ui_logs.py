import os
import logging
from flask import request, jsonify
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='/config/logs/ui.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def register_ui_log_routes(app):
    @app.route('/api/logs/add', methods=['POST'])
    def add_log():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "No log data provided"}), 400
                
            message = data.get('message', 'No message')
            level = data.get('level', 'info').lower()
            service = data.get('service', 'ui')
            
            # Map level string to logging function
            log_functions = {
                'debug': logging.debug,
                'info': logging.info,
                'warning': logging.warning,
                'error': logging.error,
                'critical': logging.critical
            }
            
            # Use the appropriate logging function or default to info
            log_function = log_functions.get(level, logging.info)
            log_function(f"[{service}] {message}")
            
            return jsonify({"success": True, "message": "Log added successfully"})
            
        except Exception as e:
            logging.error(f"Error adding log: {str(e)}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
