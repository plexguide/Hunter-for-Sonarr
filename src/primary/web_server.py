#!/usr/bin/env python3
"""
Web server for Huntarr
Provides a web interface to view logs in real-time, manage settings, and includes authentication
"""

import os
import time
import datetime
import pathlib
# import socket # No longer used
import json
# import signal # No longer used for reload
import sys
import qrcode
import pyotp
import base64
import io
# import requests # No longer used
import logging
import threading
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, redirect, url_for, session
# from src.primary.config import API_URL # No longer needed directly
# Use only settings_manager
from src.primary import settings_manager
from src.primary.utils.logger import setup_logger, get_logger # Import get_logger
from src.primary.auth import (
    authenticate_request, user_exists, create_user, verify_user, create_session,
    logout, SESSION_COOKIE_NAME, is_2fa_enabled, generate_2fa_secret,
    verify_2fa_code, disable_2fa, change_username, change_password
)
# Import blueprint for common routes
from src.primary.routes.common import common_bp

# Disable Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Configure template and static paths to use the frontend directory
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'static'))

# Create Flask app
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_sessions')

# Register blueprints
app.register_blueprint(common_bp, url_prefix="/")

# Removed MAIN_PID and signal-related code

# Lock for accessing the log files
log_lock = threading.Lock()

# Root directory for log files
LOG_DIR = "/tmp/huntarr-logs"

# Removed LOG_REFRESH_INTERVAL - fetch from settings if needed per request

# Removed get_main_process_pid and trigger_settings_reload functions

@app.before_request
def before_request():
    auth_result = authenticate_request()
    if auth_result:
        return auth_result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user')
def user():
    # User account screen
    return render_template('user.html')

# Removed /settings and /logs routes if handled by index.html and JS routing
# Keep /logs if it's the actual SSE endpoint

@app.route('/logs')
def logs_stream():
    """
    Event stream for logs.
    Filter logs by app type using the 'app' query parameter.
    Example: /logs?app=sonarr
    """
    app_type = request.args.get('app', 'sonarr')  # Default to sonarr if no app specified
    web_logger = get_logger("web_server") # Use a logger for web server messages

    # Validate app_type
    if app_type not in settings_manager.KNOWN_APPS:
        web_logger.warning(f"Invalid app type '{app_type}' requested for logs. Defaulting to 'sonarr'.")
        app_type = 'sonarr'  # Default to sonarr for invalid app types

    log_file_path = settings_manager.LOG_DIR / f"huntarr-{app_type}.log"
    web_logger.info(f"Starting log stream for {app_type} from {log_file_path}")

    def generate():
        try:
            if not log_file_path.exists():
                # Create the file if it doesn't exist
                web_logger.info(f"Log file {log_file_path} not found. Creating.")
                log_file_path.touch()
                with open(log_file_path, 'a') as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{timestamp} - {app_type.upper()} - INFO - Log file created\n")

            # Initial position - start near the end (e.g., last 10KB or 100 lines)
            # Reading the whole file initially can be slow for large logs
            initial_lines = []
            try:
                with open(log_file_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    end_pos = f.tell()
                    f.seek(max(0, end_pos - 10240), os.SEEK_SET) # Read last 10KB approx
                    initial_content = f.read().decode('utf-8', errors='ignore')
                    initial_lines = initial_content.splitlines(True)[-100:] # Get last 100 lines
                    pos = end_pos
            except Exception as e:
                 web_logger.error(f"Error reading initial log content: {e}")
                 pos = 0 # Start from beginning on error

            # Send initial lines
            for line in initial_lines:
                 yield f"data: {line.strip()}\n\n"

            while True:
                # Check if file still exists (it might be rotated)
                if not log_file_path.exists():
                    web_logger.warning(f"Log file {log_file_path} disappeared. Stopping stream.")
                    break

                current_pos = 0
                lines = []
                try:
                    with log_lock:
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(pos)
                            lines = f.readlines()
                            current_pos = f.tell()
                except FileNotFoundError:
                     web_logger.warning(f"Log file {log_file_path} disappeared during read. Stopping stream.")
                     break
                except Exception as e:
                     web_logger.error(f"Error reading log file {log_file_path}: {e}")
                     # Decide whether to break or wait and retry
                     time.sleep(5)
                     continue

                if lines:
                    pos = current_pos
                    for line in lines:
                        yield f"data: {line.strip()}\n\n"
                else:
                    # No new lines, wait a bit
                    # Fetch interval from settings dynamically if desired
                    # log_refresh_interval = settings_manager.get_setting(app_type, "log_refresh_interval_seconds", 1)
                    time.sleep(1) # Check every second

        except Exception as e:
            web_logger.error(f"Error in log stream generator for {app_type}: {e}", exc_info=True)
        finally:
            web_logger.info(f"Stopping log stream for {app_type}")

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        # Return all settings using the new manager function
        all_settings = settings_manager.load_all_app_settings()
        return jsonify(all_settings)

    elif request.method == 'POST':
        data = request.json
        web_logger = get_logger("web_server")
        web_logger.debug(f"Received settings save request: {data}")

        # Expecting data format like: { "sonarr": { "api_url": "...", ... } }
        if not isinstance(data, dict) or len(data) != 1:
            return jsonify({"success": False, "error": "Invalid payload format. Expected {'app_name': {settings...}}"}), 400

        app_name = list(data.keys())[0]
        settings_data = data[app_name]

        if app_name not in settings_manager.KNOWN_APPS:
             # Allow saving settings for potentially unknown apps if needed, or return error
             web_logger.warning(f"Attempting to save settings for unknown app: {app_name}")
             # return jsonify({"success": False, "error": f"Unknown application type: {app_name}"}), 400

        if not isinstance(settings_data, dict):
            return jsonify({"success": False, "error": "Invalid settings data format for app."}), 400

        # Save settings for the specific app
        success = settings_manager.save_app_settings(app_name, settings_data)

        if success:
            # Return the full updated config, as the frontend expects it
            all_settings = settings_manager.load_all_app_settings()
            return jsonify(all_settings)
        else:
            return jsonify({"success": False, "error": f"Failed to save settings for {app_name}"}), 500

@app.route('/api/settings/theme', methods=['GET', 'POST'])
def api_theme():
    # Theme settings are handled separately, potentially in /config/ui.json
    if request.method == 'GET':
        dark_mode = settings_manager.get_setting("ui", "dark_mode", False)
        return jsonify({"dark_mode": dark_mode})
    elif request.method == 'POST':
        data = request.json
        dark_mode = data.get('dark_mode', False)
        success = settings_manager.update_setting("ui", "dark_mode", dark_mode)
        return jsonify({"success": success})

@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    data = request.json
    app_name = data.get('app')
    web_logger = get_logger("web_server")

    if not app_name or app_name not in settings_manager.KNOWN_APPS:
        return jsonify({"success": False, "error": f"Invalid or missing app name: {app_name}"}), 400

    web_logger.info(f"Resetting settings for {app_name} to defaults.")
    # Load default settings for the app
    default_settings = settings_manager.load_default_app_settings(app_name)

    if not default_settings:
         return jsonify({"success": False, "error": f"Could not load default settings for {app_name}"}), 500

    # Save the default settings, overwriting the current ones
    success = settings_manager.save_app_settings(app_name, default_settings)

    if success:
        # Return the full updated config after reset
        all_settings = settings_manager.load_all_app_settings()
        return jsonify(all_settings)
    else:
        return jsonify({"success": False, "error": f"Failed to save reset settings for {app_name}"}), 500

@app.route('/api/app-settings', methods=['GET'])
def api_app_settings():
    app_type = request.args.get('app')
    if not app_type or app_type not in settings_manager.KNOWN_APPS:
        return jsonify({"success": False, "error": f"Invalid or missing app type: {app_type}"}), 400

    # Get API credentials using the updated settings_manager function
    api_details = settings_manager.get_api_details(app_type)
    return jsonify({"success": True, **api_details})

@app.route('/api/configured-apps', methods=['GET'])
def api_configured_apps():
    # Return the configured status of all apps using the updated settings_manager function
    configured_apps = settings_manager.list_configured_apps()
    return jsonify(configured_apps)

# --- Add Status Endpoint --- #
@app.route('/api/status/<app_name>', methods=['GET'])
def api_app_status(app_name):
    """Check connection status for a specific app."""
    web_logger = get_logger("web_server")
    if app_name not in settings_manager.KNOWN_APPS:
        return jsonify({"configured": False, "connected": False, "error": "Invalid app name"}), 400

    api_details = settings_manager.get_api_details(app_name)
    is_configured = bool(api_details.get('api_url') and api_details.get('api_key'))
    is_connected = False

    if is_configured:
        try:
            api_module = importlib.import_module(f'src.primary.apps.{app_name}.api')
            check_connection = getattr(api_module, 'check_connection')
            # Pass URL and Key explicitly
            is_connected = check_connection(api_details['api_url'], api_details['api_key'])
        except (ImportError, AttributeError):
            web_logger.error(f"Could not find check_connection function for {app_name}.")
        except Exception as e:
            web_logger.error(f"Error checking connection for {app_name}: {e}")

    return jsonify({"configured": is_configured, "connected": is_connected})

# --- Add Hunt Control Endpoints --- #
# These might need adjustment depending on how start/stop is managed now
# If main.py handles threads based on config, these might not be needed,
# or they could modify a global 'enabled' setting per app.
# For now, keep them simple placeholders.

@app.route('/api/hunt/start', methods=['POST'])
def api_start_hunt():
    # Placeholder: In the new model, threads start based on config.
    # This might enable all configured apps or toggle a global flag.
    # Or it could modify an 'enabled' setting per app.
    # settings_manager.update_setting('global', 'hunt_enabled', True)
    return jsonify({"success": True, "message": "Hunt control endpoint (start) - functionality may change."})

@app.route('/api/hunt/stop', methods=['POST'])
def api_stop_hunt():
    # Placeholder: Signal main thread to stop?
    # Or disable all apps?
    # settings_manager.update_setting('global', 'hunt_enabled', False)
    # Or send SIGTERM/SIGINT to the main process?
    # pid = get_main_process_pid() # Need a way to get PID if not self
    # if pid: os.kill(pid, signal.SIGTERM)
    return jsonify({"success": True, "message": "Hunt control endpoint (stop) - functionality may change."})


def start_web_server():
    """Start the web server in debug or production mode"""
    web_logger = get_logger("web_server")
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    host = '0.0.0.0'  # Listen on all interfaces
    port = int(os.environ.get('PORT', 9705))

    # Ensure the log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    web_logger.info(f"Starting web server on {host}:{port} (Debug: {debug_mode})")
    # In production, use Werkzeug's simple server or a proper WSGI server
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False)

# if __name__ == '__main__':
#     start_web_server() # Usually started by a different entry point