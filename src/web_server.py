#!/usr/bin/env python3
"""
Web server for Huntarr-Sonarr
Provides a web interface to view logs in real-time and manage settings
"""

import os
import time
import datetime
import pathlib
import socket
import json
import signal
import sys
from flask import Flask, render_template, Response, stream_with_context, request, jsonify, send_from_directory
import logging
from config import ENABLE_WEB_UI
import settings_manager
from utils.logger import setup_logger

# Check if web UI is disabled
if not ENABLE_WEB_UI:
    print("Web UI is disabled. Exiting web server.")
    exit(0)

# Disable Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Log file location
LOG_FILE = "/tmp/huntarr-logs/huntarr.log"
LOG_DIR = pathlib.Path("/tmp/huntarr-logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Get the PID of the main process
def get_main_process_pid():
    try:
        # Try to find the main.py process
        for proc in os.listdir('/proc'):
            if not proc.isdigit():
                continue
            try:
                with open(f'/proc/{proc}/cmdline', 'r') as f:
                    cmdline = f.read().replace('\0', ' ')
                    if 'python' in cmdline and 'main.py' in cmdline:
                        return int(proc)
            except (IOError, ProcessLookupError):
                continue
        return None
    except:
        return None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('../frontend/static', path)

@app.route('/logs')
def stream_logs():
    """Stream logs to the client"""
    def generate():
        # First get all existing logs
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                # Read the last 100 lines of the log file
                lines = f.readlines()[-100:]
                for line in lines:
                    yield f"data: {line}\n\n"
        
        # Then stream new logs as they appear
        with open(LOG_FILE, 'r') as f:
            # Move to the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line}\n\n"
                else:
                    time.sleep(0.1)

    return Response(stream_with_context(generate()), 
                   mimetype='text/event-stream')

def get_ip_address():
    """Get the host's IP address from API_URL for display"""
    try:
        from urllib.parse import urlparse
        from config import API_URL
        
        # Extract the hostname/IP from the API_URL
        parsed_url = urlparse(API_URL)
        hostname = parsed_url.netloc
        
        # Remove port if present
        if ':' in hostname:
            hostname = hostname.split(':')[0]
            
        return hostname
    except Exception as e:
        # Fallback to the current method if there's an issue
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except:
            return "localhost"

if __name__ == "__main__":
    # Create a basic log entry at startup
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = get_ip_address()
    
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - huntarr-web - INFO - Web server starting on port 9705\n")
        f.write(f"{timestamp} - huntarr-web - INFO - Web interface available at http://{ip_address}:9705\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=9705, debug=False, threaded=True)