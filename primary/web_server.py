#!/usr/bin/env python3
"""
Web server for Huntarr
Provides a web interface to view logs in real-time, manage settings, and includes authentication
"""

import os
import time
import datetime
import pathlib
import socket
import json
import signal
import sys
import qrcode
import pyotp
import base64
import io
import requests
import logging
import threading
from flask import Flask, render_template, request, jsonify, Response, send_from_directory, redirect, url_for, session
from primary.config import API_URL
from primary import settings_manager, keys_manager
from primary.utils.logger import setup_logger
from primary.auth import (
    authenticate_request, user_exists, create_user, verify_user, create_session, 
    logout, SESSION_COOKIE_NAME, is_2fa_enabled, generate_2fa_secret, 
    verify_2fa_code, disable_2fa, change_username, change_password
)
# Import blueprint for common routes
from primary.routes.common import common_bp

# Disable Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_sessions')

# Register blueprints
app.register_blueprint(common_bp, url_prefix="/")

# Global main process PID
MAIN_PID = os.getpid()

# Lock for accessing the log files
log_lock = threading.Lock()

# Root directory for log files
LOG_DIR = "/tmp/huntarr-logs"

# Default log refresh interval (seconds)
LOG_REFRESH_INTERVAL = settings_manager.get_setting("huntarr", "log_refresh_interval_seconds", 30)

# Function to get the PID of the main python process
def get_main_process_pid():
    return MAIN_PID

# Function to trigger reload of settings for a specific app
def trigger_settings_reload(app_type):
    """
    Trigger a settings reload for a specific app by sending a SIGUSR1 signal to the main process
    with the app type set in an environment variable.
    
    Args:
        app_type: The app type to reload settings for (sonarr, radarr, etc.)
    """
    # Set environment variable for the app type to restart
    os.environ["RESTART_APP_TYPE"] = app_type
    
    # Send SIGUSR1 to the main process
    pid = get_main_process_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGUSR1)
            return True
        except Exception as e:
            print(f"Error sending signal to process {pid}: {e}")
    return False

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

@app.route('/settings')
def settings():
    # Redirect to the home page with settings tab active
    return render_template('index.html')

@app.route('/logs')
def logs():
    """
    Event stream for logs. 
    Filter logs by app type using the 'app' query parameter.
    Example: /logs?app=sonarr
    """
    app_type = request.args.get('app', 'sonarr')  # Default to sonarr if no app specified
    
    # Validate app_type
    if app_type not in ['sonarr', 'radarr', 'lidarr', 'readarr']:
        app_type = 'sonarr'  # Default to sonarr for invalid app types
    
    def generate():
        # Get the specific log file for the app type
        log_file_path = f"{LOG_DIR}/huntarr-{app_type}.log"
        if not os.path.exists(log_file_path):
            # Create the file if it doesn't exist
            with open(log_file_path, 'a') as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - {app_type} - INFO - Log file created\n")
        
        # Initial position - start at the end of the file
        with open(log_file_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()
        
        while True:
            with log_lock:
                with open(log_file_path, 'r') as f:
                    f.seek(pos)
                    lines = f.readlines()
                    pos = f.tell()
            
            if lines:
                for line in lines:
                    # Check if the line contains the app_type
                    if f" - {app_type} - " in line or " - huntarr - " in line:
                        yield f"data: {line}\n\n"
            
            time.sleep(1)  # Check for new logs every second
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        # Return all settings
        return jsonify(settings_manager.get_all_settings())
    elif request.method == 'POST':
        # Save settings and trigger reload for the specific app type
        data = request.json
        app_type = data.get('app_type', 'sonarr')
        
        result = settings_manager.save_settings(data)
        
        # Trigger reload for the specific app type
        if result.get('success', False):
            reload_success = trigger_settings_reload(app_type)
            if not reload_success:
                result['message'] = "Settings saved but failed to trigger reload"
        
        return jsonify(result)

@app.route('/api/settings/theme', methods=['GET', 'POST'])
def api_theme():
    if request.method == 'GET':
        # Return current theme setting
        dark_mode = settings_manager.get_setting("ui", "dark_mode", False)
        return jsonify({"dark_mode": dark_mode})
    elif request.method == 'POST':
        # Save theme setting
        data = request.json
        dark_mode = data.get('dark_mode', False)
        settings_manager.set_setting("ui", "dark_mode", dark_mode)
        return jsonify({"success": True})

@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    data = request.json
    app_type = data.get('app', 'sonarr')
    
    # Reset settings for the specific app type
    settings_manager.reset_settings(app_type)
    
    # Trigger reload for the specific app type
    reload_success = trigger_settings_reload(app_type)
    
    return jsonify({"success": True, "reload_triggered": reload_success})

@app.route('/api/app-settings', methods=['GET'])
def api_app_settings():
    app_type = request.args.get('app', 'sonarr')
    
    # Validate app_type
    if app_type not in ['sonarr', 'radarr', 'lidarr', 'readarr']:
        return jsonify({"success": False, "message": f"Invalid app type: {app_type}"})
    
    # Get API credentials for the specified app type
    api_url, api_key = keys_manager.get_api_keys(app_type)
    
    return jsonify({
        "success": True,
        "api_url": api_url,
        "api_key": api_key
    })

@app.route('/api/configured-apps', methods=['GET'])
def api_configured_apps():
    # Return the configured status of all apps
    configured_apps = keys_manager.get_configured_apps()
    return jsonify(configured_apps)

def start_web_server():
    """Start the web server in debug or production mode"""
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    host = '0.0.0.0'  # Listen on all interfaces
    port = int(os.environ.get('PORT', 9705))
    
    # Ensure the log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # In production, use Werkzeug's simple server
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False)

if __name__ == '__main__':
    start_web_server()