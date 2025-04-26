#!/usr/bin/env python3
"""
Web server for Huntarr
Provides a web interface to view logs in real-time, manage settings, and includes authentication
"""

import asyncio
import os
import datetime
from threading import Lock
from primary.utils.logger import LOG_DIR, APP_LOG_FILES, MAIN_LOG_FILE # Import log constants
from primary import settings_manager # Import settings_manager

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
import importlib # Added import
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, redirect, url_for, session
# from src.primary.config import API_URL # No longer needed directly
# Use only settings_manager
from src.primary import settings_manager
from src.primary.utils.logger import setup_logger, get_logger, LOG_DIR # Import get_logger and LOG_DIR
from src.primary.auth import (
    authenticate_request, user_exists, create_user, verify_user, create_session,
    logout, SESSION_COOKIE_NAME, is_2fa_enabled, generate_2fa_secret,
    verify_2fa_code, disable_2fa, change_username, change_password
)
# Import blueprint for common routes
from src.primary.routes.common import common_bp

# Import blueprints for each app from the centralized blueprints module
from src.primary.apps.blueprints import sonarr_bp, radarr_bp, lidarr_bp, readarr_bp, whisparr_bp

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
app.register_blueprint(common_bp)
app.register_blueprint(sonarr_bp, url_prefix='/api/sonarr')
app.register_blueprint(radarr_bp, url_prefix='/api/radarr')
app.register_blueprint(lidarr_bp, url_prefix='/api/lidarr')
app.register_blueprint(readarr_bp, url_prefix='/api/readarr')
app.register_blueprint(whisparr_bp, url_prefix='/api/whisparr')

# Register the authentication check to run before requests
app.before_request(authenticate_request)

# Removed MAIN_PID and signal-related code

# Lock for accessing the log files
log_lock = Lock()

# Define known log files based on logger config
KNOWN_LOG_FILES = {
    "sonarr": APP_LOG_FILES.get("sonarr"),
    "radarr": APP_LOG_FILES.get("radarr"),
    "lidarr": APP_LOG_FILES.get("lidarr"),
    "readarr": APP_LOG_FILES.get("readarr"),
    "whisparr": APP_LOG_FILES.get("whisparr"),
    "system": MAIN_LOG_FILE, # Map 'system' to the main huntarr log
}
# Filter out None values if an app log file doesn't exist
KNOWN_LOG_FILES = {k: v for k, v in KNOWN_LOG_FILES.items() if v}

ALL_APP_LOG_FILES = list(KNOWN_LOG_FILES.values()) # List of all individual log file paths

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
    Supports 'all', 'system', 'sonarr', 'radarr', 'lidarr', 'readarr'.
    Example: /logs?app=sonarr
    """
    app_type = request.args.get('app', 'all')  # Default to 'all' if no app specified
    web_logger = get_logger("web_server")

    valid_app_types = list(KNOWN_LOG_FILES.keys()) + ['all']
    if app_type not in valid_app_types:
        web_logger.warning(f"Invalid app type '{app_type}' requested for logs. Defaulting to 'all'.")
        app_type = 'all'

    # Use a client identifier to track connections
    client_id = request.remote_addr
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    web_logger.info(f"Starting log stream for app type: {app_type} (client: {client_id}, time: {current_time})")

    # Import needed modules
    import time
    from pathlib import Path
    import threading

    # Track active connections to limit resource usage
    if not hasattr(app, 'active_log_streams'):
        app.active_log_streams = {}
        app.log_stream_lock = threading.Lock()

    # Clean up stale connections (older than 60 seconds without activity)
    with app.log_stream_lock:
        current_time = time.time()
        stale_clients = [c for c, t in app.active_log_streams.items() 
                         if current_time - t > 60]
        for client in stale_clients:
            app.active_log_streams.pop(client, None)
            web_logger.debug(f"Removed stale log stream connection for client: {client}")
        
        # Update this client's timestamp
        app.active_log_streams[client_id] = current_time
        
        # If too many connections, return an error for new ones
        if len(app.active_log_streams) > 10:  # Limit to 10 concurrent connections
            oldest_client = min(app.active_log_streams.items(), key=lambda x: x[1])[0]
            if client_id != oldest_client and len(app.active_log_streams) > 3:
                web_logger.warning(f"Too many log stream connections ({len(app.active_log_streams)}). Rejecting new connection from {client_id}")
                return Response("data: Too many active connections. Please try again later.\n\n", 
                               mimetype='text/event-stream')

    def generate():
        """Generate log events for the SSE stream."""
        try:
            # Initialize last activity time
            last_activity = time.time()
            
            # Determine which log files to follow
            if app_type == 'all':
                log_files_to_follow = list(KNOWN_LOG_FILES.items())
            else:
                log_file = KNOWN_LOG_FILES.get(app_type)
                if log_file:
                    log_files_to_follow = [(app_type, log_file)]
                else:
                    web_logger.warning(f"No log file found for app type: {app_type}")
                    yield f"data: No logs available for {app_type}\n\n"
                    return

            # Send a connection confirmation message
            yield f"data: Starting log stream for {app_type}...\n\n"

            # Track file positions for each log
            positions = {}
            last_check = {}
            
            # Keep-alive counter to send periodic keep-alive messages
            keep_alive_counter = 0
            
            # Convert string paths to Path objects
            log_files_to_follow = [(name, Path(path) if isinstance(path, str) else path) 
                                  for name, path in log_files_to_follow]

            # Main log streaming loop
            while True:
                had_content = False
                current_time = time.time()
                
                # Update client activity timestamp periodically
                if current_time - last_activity > 10:
                    with app.log_stream_lock:
                        app.active_log_streams[client_id] = current_time
                    last_activity = current_time
                
                # Increment keep-alive counter
                keep_alive_counter += 1
                
                # Check each log file
                for name, path in log_files_to_follow:
                    try:
                        # Skip checking too frequently to reduce CPU usage
                        now = datetime.datetime.now()
                        if name in last_check and (now - last_check[name]).total_seconds() < 0.5:  # Reduced polling frequency
                            continue
                        
                        last_check[name] = now
                        
                        # Check if file exists
                        if not path.exists():
                            continue

                        # Get current size to detect truncation
                        current_size = path.stat().st_size
                        
                        # Initialize position if needed or handle truncation
                        if name not in positions or current_size < positions[name]:
                            # For initial connection or truncated file, start from end minus 10KB 
                            # but use a smaller value (5KB) to reduce initial load
                            positions[name] = max(0, current_size - 5120)
                                
                        # Read new content - use a with block for proper resource cleanup
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(positions[name])
                            # Read a limited number of lines at once to prevent memory issues
                            new_lines = []
                            for _ in range(100):  # Limit to 100 lines per check
                                line = f.readline()
                                if not line:
                                    break
                                new_lines.append(line)
                            
                            if new_lines:
                                had_content = True
                                positions[name] = f.tell()
                                for line in new_lines:
                                    if line.strip():  # Only send non-empty lines
                                        yield f"data: {line.strip()}\n\n"
                    except Exception as e:
                        web_logger.error(f"Error reading log file {path}: {e}")
                        yield f"data: ERROR: Problem reading {name} log: {str(e)}\n\n"
                        # Reset position on error
                        positions.pop(name, None)
                
                # Send a keep-alive comment every ~30 seconds to prevent timeout
                # but only if we haven't had any real content
                if not had_content:
                    if keep_alive_counter >= 60:  # ~30 seconds (60 * 0.5s sleep)
                        yield f": keepalive {time.time()}\n\n"  # Send a comment (prefixed with :) that won't display
                        keep_alive_counter = 0
                    
                    # Sleep between checks to prevent high CPU usage
                    time.sleep(0.5)
                else:
                    # Reset keep-alive counter when we've sent actual content
                    keep_alive_counter = 0
                    # Shorter sleep when actively sending content
                    time.sleep(0.1)
        except GeneratorExit:
            # Clean up when client disconnects
            with app.log_stream_lock:
                app.active_log_streams.pop(client_id, None)
            web_logger.info(f"Client {client_id} disconnected from log stream for {app_type}")
        except Exception as e:
            web_logger.error(f"Error in log stream generator: {e}", exc_info=True)
            yield f"data: ERROR: Log streaming failed: {str(e)}\n\n"
            
            # Clean up on error
            with app.log_stream_lock:
                app.active_log_streams.pop(client_id, None)

    # Return the SSE response with appropriate headers for better streaming
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering if using nginx
    return response

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        # Return all settings using the new manager function
        all_settings = settings_manager.get_all_settings() # Corrected function name
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

        if app_name not in settings_manager.KNOWN_APP_TYPES: # Corrected attribute name
             # Allow saving settings for potentially unknown apps if needed, or return error
             # For now, let's restrict to known types
             return jsonify({"success": False, "error": f"Unknown application type: {app_name}"}), 400

        # Save the settings using the manager
        success = settings_manager.save_settings(app_name, settings_data) # Corrected function name

        if success:
            # Return the full updated configuration
            all_settings = settings_manager.get_all_settings() # Corrected: Use get_all_settings
            return jsonify(all_settings) # Return the full config object
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

    if not app_name or app_name not in settings_manager.KNOWN_APP_TYPES: # Corrected attribute name
        return jsonify({"success": False, "error": f"Invalid or missing app name: {app_name}"}), 400

    web_logger.info(f"Resetting settings for {app_name} to defaults.")
    # Load default settings for the app
    default_settings = settings_manager.load_default_app_settings(app_name)

    if not default_settings:
         return jsonify({"success": False, "error": f"Could not load default settings for {app_name}"}), 500

    # Save the default settings, overwriting the current ones
    success = settings_manager.save_settings(app_name, default_settings) # Corrected function name

    if success:
        # Return the full updated config after reset
        all_settings = settings_manager.get_all_settings() # Corrected function name
        return jsonify(all_settings)
    else:
        return jsonify({"success": False, "error": f"Failed to save reset settings for {app_name}"}), 500

@app.route('/api/app-settings', methods=['GET'])
def api_app_settings():
    app_type = request.args.get('app')
    if not app_type or app_type not in settings_manager.KNOWN_APP_TYPES: # Corrected attribute name
        return jsonify({"success": False, "error": f"Invalid or missing app type: {app_type}"}), 400

    # Get API credentials using the updated settings_manager function
    # api_details = settings_manager.get_api_details(app_type) # Function does not exist
    api_url = settings_manager.get_api_url(app_type)
    api_key = settings_manager.get_api_key(app_type)
    api_details = {"api_url": api_url, "api_key": api_key}
    return jsonify({"success": True, **api_details})

@app.route('/api/configured-apps', methods=['GET'])
def api_configured_apps():
    # Return the configured status of all apps using the updated settings_manager function
    configured_apps_list = settings_manager.get_configured_apps() # Corrected function name
    # Convert list to dict format expected by frontend
    configured_status = {app: (app in configured_apps_list) for app in settings_manager.KNOWN_APP_TYPES}
    return jsonify(configured_status)

# --- Add Status Endpoint --- #
@app.route('/api/status/<app_name>', methods=['GET'])
def api_app_status(app_name):
    """Check connection status for a specific app."""
    web_logger = get_logger("web_server")
    if app_name not in settings_manager.KNOWN_APP_TYPES: # Corrected attribute name
        return jsonify({"configured": False, "connected": False, "error": "Invalid app name"}), 400

    # api_details = settings_manager.get_api_details(app_name) # Function does not exist
    api_url = settings_manager.get_api_url(app_name)
    api_key = settings_manager.get_api_key(app_name)
    is_configured = bool(api_url and api_key)
    is_connected = False
    api_timeout = settings_manager.get_setting(app_name, "api_timeout", 10) # Get api_timeout, default to 10

    if is_configured:
        try:
            api_module = importlib.import_module(f'src.primary.apps.{app_name}.api')
            check_connection = getattr(api_module, 'check_connection')
            # Pass URL, Key, and Timeout explicitly
            is_connected = check_connection(api_url, api_key, api_timeout) # Pass api_timeout
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
    web_logger.info("--- start_web_server function called ---") # Added log
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    host = '0.0.0.0'  # Listen on all interfaces
    port = int(os.environ.get('PORT', 9705))

    # Ensure the log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    web_logger.info(f"Attempting to start web server on {host}:{port} (Debug: {debug_mode})") # Modified log
    # In production, use Werkzeug's simple server or a proper WSGI server
    web_logger.info("--- Calling app.run() ---") # Added log
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False) # Keep this line if needed for direct execution testing, but it's now handled by root main.py