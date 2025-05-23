from flask import Flask, render_template, request, redirect, jsonify, url_for
import os
import json
import datetime

# Import the necessary functions
from src.primary.stateful_manager import reset_stateful_management, get_stateful_management_info
from src.primary.cycle_tracker import get_cycle_status, reset_cycle
from src.primary.utils.config_paths import get_reset_path

# Configure Flask to use templates and static files from the frontend folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# API Routes

@app.route('/api/cycle/status', methods=['GET'])
def api_get_all_cycle_status():
    """API endpoint to get cycle status for all apps."""
    try:
        status = get_cycle_status()
        return jsonify(status), 200
    except Exception as e:
        app.logger.error(f"Error getting cycle status: {e}")
        return jsonify({"error": "Failed to retrieve cycle status information."}), 500

@app.route('/api/cycle/status/<app_name>', methods=['GET'])
def api_get_app_cycle_status(app_name):
    """API endpoint to get cycle status for a specific app."""
    try:
        status = get_cycle_status(app_name)
        return jsonify(status), 200
    except Exception as e:
        app.logger.error(f"Error getting cycle status for {app_name}: {e}")
        return jsonify({"error": f"Failed to retrieve cycle status for {app_name}."}), 500

@app.route('/api/cycle/reset/<app_name>', methods=['POST'])
def api_reset_app_cycle(app_name):
    """API endpoint to reset a specific app's cycle."""
    try:
        # Reset the cycle in the tracker
        success = reset_cycle(app_name)
        
        # Use cross-platform path for reset file
        reset_file_path = get_reset_path(app_name)
        
        # Create reset trigger file
        try:
            with open(reset_file_path, 'w') as f:
                f.write(f"Reset triggered at {datetime.now().isoformat()}")
        except Exception as e:
            app.logger.error(f"Error creating reset file for {app_name}: {e}")
            return jsonify({'success': False, 'message': f'Failed to reset cycle for {app_name}: {e}'}), 500
        
        return jsonify({'success': True, 'message': f'Cycle reset for {app_name}.'})
    except Exception as e:
        app.logger.error(f"Error resetting cycle for {app_name}: {e}")
        return jsonify({'success': False, 'message': f'Failed to reset cycle for {app_name}: {e}'}), 500

@app.route('/api/stateful/reset', methods=['POST'])
def api_reset_stateful():
    """API endpoint to reset the stateful management system."""
    success = reset_stateful_management()
    if success:
        return jsonify({"success": True, "message": "Stateful management reset successfully."}), 200
    else:
        return jsonify({"success": False, "message": "Failed to reset stateful management."}), 500

@app.route('/api/stateful/info', methods=['GET'])
def api_get_stateful_info():
    """API endpoint to get stateful management info."""
    try:
        info = get_stateful_management_info()
        return jsonify(info), 200
    except Exception as e:
        # Log the exception details if possible
        app.logger.error(f"Error getting stateful info: {e}")
        return jsonify({"error": "Failed to retrieve stateful information."}), 500

def get_ui_preference():
    """Determine which UI to use based on config and user preference"""
    # Check if ui_settings.json exists
    config_file = os.path.join(os.path.dirname(__file__), 'config/ui_settings.json')
    
    use_new_ui = False
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)
                use_new_ui = settings.get('use_new_ui', False)
        except Exception as e:
            print(f"Error loading UI settings: {e}")
    
    # Allow URL parameter to override
    ui_param = request.args.get('ui', None)
    if ui_param == 'new':
        use_new_ui = True
    elif ui_param == 'classic':
        use_new_ui = False
    
    return use_new_ui

@app.route('/')
def index():
    """Root route with UI switching capability"""
    if get_ui_preference():
        return redirect('/new')
    else:
        return render_template('index.html')

@app.route('/user')
def user_page():
    """User settings page with UI switching capability"""
    if get_ui_preference():
        return redirect(url_for("user_page_new"))
    else:
        return render_template('user.html')

@app.route('/user/new')
def user_page_new():
    """Serve the new user settings page"""
    return render_template('user-new.html')

if __name__ == '__main__':
    app.run(debug=True)