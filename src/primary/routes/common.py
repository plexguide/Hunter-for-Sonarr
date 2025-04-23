#!/usr/bin/env python3
"""
Common routes blueprint for Huntarr web interface
"""

import os
import json
import base64
import io
import qrcode
import pyotp
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, Response, send_from_directory
from src.primary import settings_manager # Use the updated settings manager
from src.primary.auth import (
    user_exists, create_user, verify_user, create_session, logout,
    SESSION_COOKIE_NAME, is_2fa_enabled, generate_2fa_secret,
    verify_2fa_code, disable_2fa, change_username, change_password
)

# Get logger for common routes
logger = logging.getLogger("common_routes")

common_bp = Blueprint('common', __name__,
                      template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'templates')),
                      static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'static')))

# --- Static File Serving --- #

@common_bp.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(common_bp.static_folder, filename)

@common_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(common_bp.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@common_bp.route('/logo/<path:filename>')
def logo_files(filename):
    logo_dir = os.path.join(common_bp.static_folder, 'logo')
    return send_from_directory(logo_dir, filename)

# --- Authentication Routes --- #

@common_bp.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        otp_code = data.get('otp_code')

        user_data = verify_user(username, password)
        if user_data:
            if is_2fa_enabled(username):
                if not otp_code:
                    # 2FA enabled, but no code provided - prompt for it
                    return jsonify({"success": False, "requires_2fa": True})
                
                if verify_2fa_code(username, otp_code):
                    # 2FA verified
                    session_token = create_session(username)
                    response = jsonify({"success": True})
                    response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, samesite='Lax')
                    return response
                else:
                    # Invalid 2FA code
                    return jsonify({"success": False, "error": "Invalid 2FA code"}), 401
            else:
                # 2FA not enabled, login successful
                session_token = create_session(username)
                response = jsonify({"success": True})
                response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, samesite='Lax')
                return response
        else:
            # Invalid username or password
            return jsonify({"success": False, "error": "Invalid username or password"}), 401
    else:
        # GET request - show login page
        return render_template('login.html')

@common_bp.route('/logout', methods=['POST'])
def logout_route():
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        logout(session_token)
    response = jsonify({"success": True})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response

@common_bp.route('/setup', methods=['GET', 'POST'])
def setup_route():
    if user_exists():
        # If a user already exists, redirect to login or home
        return redirect(url_for('common.login_route'))

    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400

        if create_user(username, password):
            # Automatically log in the user after setup
            session_token = create_session(username)
            response = jsonify({"success": True})
            response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, samesite='Lax')
            return response
        else:
            return jsonify({"success": False, "error": "Failed to create user"}), 500
    else:
        # GET request - show setup page
        return render_template('setup.html')

# --- User Management API Routes --- #

@common_bp.route('/api/user/info', methods=['GET'])
def get_user_info():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not authenticated"}), 401
    
    two_fa_status = is_2fa_enabled(username)
    return jsonify({"username": username, "is_2fa_enabled": two_fa_status})

@common_bp.route('/api/user/change-username', methods=['POST'])
def change_username_route():
    current_username = session.get('username')
    if not current_username:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    new_username = data.get('new_username')
    password = data.get('password')

    if not new_username or not password:
        return jsonify({"success": False, "error": "New username and password are required"}), 400

    if change_username(current_username, new_username, password):
        # Update session username
        session['username'] = new_username
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to change username. Check password or if username is taken."}), 400

@common_bp.route('/api/user/change-password', methods=['POST'])
def change_password_route():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"success": False, "error": "Current and new passwords are required"}), 400

    if change_password(username, current_password, new_password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to change password. Check current password."}), 400

# --- 2FA Management API Routes --- #

@common_bp.route('/api/user/2fa/setup', methods=['POST'])
def setup_2fa():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not authenticated"}), 401

    secret, uri = generate_2fa_secret(username)
    
    # Generate QR code
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return jsonify({"success": True, "secret": secret, "qr_code": qr_code_base64})

@common_bp.route('/api/user/2fa/verify', methods=['POST'])
def verify_2fa():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    otp_code = data.get('otp_code')

    if not otp_code:
        return jsonify({"success": False, "error": "OTP code is required"}), 400

    # verify_2fa_code also enables 2FA if successful
    if verify_2fa_code(username, otp_code, enable_on_verify=True):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Invalid OTP code"}), 400

@common_bp.route('/api/user/2fa/disable', methods=['POST'])
def disable_2fa_route():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    password = data.get('password') # Require password to disable 2FA

    if not password:
        return jsonify({"success": False, "error": "Password is required to disable 2FA"}), 400

    if disable_2fa(username, password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to disable 2FA. Check password."}), 400

# Note: Settings and status routes previously here are now likely handled directly in web_server.py
# or should be updated here if they remain in this blueprint.
# Example: If /api/settings was here, it would need updating:
#
# @common_bp.route('/api/settings', methods=['GET', 'POST'])
# def api_settings():
#     if request.method == 'GET':
#         all_settings = settings_manager.load_all_app_settings()
#         return jsonify(all_settings)
#     elif request.method == 'POST':
#         data = request.json
#         # ... (logic as in web_server.py) ...
#         app_name = list(data.keys())[0]
#         settings_data = data[app_name]
#         success = settings_manager.save_app_settings(app_name, settings_data)
#         if success:
#             all_settings = settings_manager.load_all_app_settings()
#             return jsonify(all_settings)
#         else:
#             return jsonify({"success": False, "error": f"Failed to save settings for {app_name}"}), 500

# Ensure all routes previously in this file that interact with settings
# are either moved to web_server.py or updated here using the new settings_manager functions.

"""
Common API routes for Huntarr web interface
"""

from flask import Blueprint, request, jsonify, current_app
from src.primary import settings_manager # Import the updated settings manager
from src.primary.utils.logger import logger # Use the central logger
from src.primary.auth import token_required
from src.primary.apps.sonarr import api as sonarr_api # Keep for connection check example
from src.primary.apps.radarr import api as radarr_api # Keep for connection check example
# Add imports for other app APIs if needed for connection checks

common_bp = Blueprint('common', __name__, url_prefix='/api')

# --- Settings Routes --- #

@common_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    """Get all settings for all applications."""
    try:
        all_settings = settings_manager.get_all_settings()
        # Optionally filter or structure settings before sending to frontend
        # For now, send everything loaded
        return jsonify(all_settings)
    except Exception as e:
        logger.error(f"Error getting all settings: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve settings"}), 500

@common_bp.route('/settings', methods=['POST'])
@token_required
def update_settings(current_user):
    """Update settings for one or more applications."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    results = {}
    has_errors = False

    # Expecting data in the format: { "sonarr": { ... }, "radarr": { ... }, "ui": { ... } }
    for app_name, settings_data in data.items():
        if app_name in settings_manager.KNOWN_APP_TYPES or app_name == "ui": # Allow saving UI settings too
            logger.info(f"Received settings update for: {app_name}")
            if settings_manager.save_settings(app_name, settings_data):
                results[app_name] = "Settings saved successfully."
                logger.info(f"Successfully saved settings for {app_name}.")
            else:
                results[app_name] = f"Failed to save settings for {app_name}."
                logger.error(f"Failed to save settings for {app_name}.")
                has_errors = True
        else:
            results[app_name] = f"Unknown application type: {app_name}"
            logger.warning(f"Received settings for unknown application type: {app_name}")
            # Decide if this is an error or just ignore
            # has_errors = True 

    if has_errors:
        return jsonify({"message": "Settings update processed with errors.", "details": results}), 500
    else:
        # No need to trigger reload via signal anymore, main loop handles it.
        return jsonify({"message": "Settings updated successfully.", "details": results}), 200

@common_bp.route('/settings/reset/<app_name>', methods=['POST'])
@token_required
def reset_settings(current_user, app_name):
    """Reset settings for a specific application to defaults."""
    if app_name not in settings_manager.KNOWN_APP_TYPES and app_name != "ui":
        return jsonify({"error": f"Invalid application name: {app_name}"}), 400

    try:
        default_settings = settings_manager.load_default_app_settings(app_name)
        if not default_settings:
             return jsonify({"error": f"Could not load default settings for {app_name}"}), 500
             
        if settings_manager.save_settings(app_name, default_settings):
            logger.info(f"Reset settings for {app_name} to defaults.")
            # Return the reset settings
            return jsonify({"message": f"Settings for {app_name} reset successfully.", "settings": default_settings}), 200
        else:
            logger.error(f"Failed to save reset settings for {app_name}.")
            return jsonify({"error": f"Failed to save reset settings for {app_name}"}), 500
    except Exception as e:
        logger.error(f"Error resetting settings for {app_name}: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred while resetting settings for {app_name}"}), 500

@common_bp.route('/settings/theme', methods=['GET'])
@token_required
def get_theme_setting(current_user):
    """Get the current theme setting."""
    try:
        # Assume theme is stored under a special 'ui' app settings file
        theme = settings_manager.get_setting("ui", "theme", "dark") # Default to dark
        return jsonify({"theme": theme})
    except Exception as e:
        logger.error(f"Error getting theme setting: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve theme setting"}), 500

@common_bp.route('/settings/theme', methods=['POST'])
@token_required
def update_theme_setting(current_user):
    """Update the theme setting."""
    data = request.get_json()
    if not data or 'theme' not in data:
        return jsonify({"error": "Invalid data, 'theme' key missing"}), 400

    new_theme = data['theme']
    if new_theme not in ["light", "dark"]:
        return jsonify({"error": "Invalid theme value"}), 400

    try:
        # Load current UI settings, update theme, save back
        ui_settings = settings_manager.load_settings("ui") # Load or create ui.json
        ui_settings["theme"] = new_theme
        if settings_manager.save_settings("ui", ui_settings):
            logger.info(f"Theme updated to: {new_theme}")
            return jsonify({"message": "Theme updated successfully", "theme": new_theme}), 200
        else:
            logger.error("Failed to save updated theme setting.")
            return jsonify({"error": "Failed to save theme setting"}), 500
    except Exception as e:
        logger.error(f"Error updating theme setting: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while updating the theme"}), 500

# --- Application Status and Info --- #

@common_bp.route('/configured-apps', methods=['GET'])
@token_required
def get_configured_apps(current_user):
    """Get a list of applications that are configured (API URL/Key set)."""
    try:
        apps = settings_manager.get_configured_apps()
        return jsonify(apps)
    except Exception as e:
        logger.error(f"Error getting configured apps: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve configured applications"}), 500

@common_bp.route('/status/<app_name>', methods=['GET'])
@token_required
def get_app_status(current_user, app_name):
    """Check the connection status for a specific application."""
    if app_name not in settings_manager.KNOWN_APP_TYPES:
        return jsonify({"error": f"Unknown application type: {app_name}"}), 400

    try:
        api_url = settings_manager.get_setting(app_name, "api_url")
        api_key = settings_manager.get_setting(app_name, "api_key")
        api_timeout = settings_manager.get_setting(app_name, "api_timeout", 10) # Default timeout 10s

        if not api_url or not api_key:
            return jsonify({"status": "unconfigured", "message": "API URL or Key not set."}), 200

        connected = False
        # Use the specific app's connection check function
        if app_name == "sonarr":
            connected = sonarr_api.check_connection(api_url, api_key, api_timeout)
        elif app_name == "radarr":
            connected = radarr_api.check_connection(api_url, api_key, api_timeout)
        # Add elif for lidarr, readarr etc.
        # elif app_name == "lidarr":
        #     connected = lidarr_api.check_connection(api_url, api_key, api_timeout)
        # elif app_name == "readarr":
        #     connected = readarr_api.check_connection(api_url, api_key, api_timeout)
        else:
             return jsonify({"status": "unknown", "message": f"Connection check not implemented for {app_name}."}), 501

        if connected:
            return jsonify({"status": "connected", "message": f"Successfully connected to {app_name}."}), 200
        else:
            return jsonify({"status": "error", "message": f"Failed to connect to {app_name}. Check URL, Key, and network."}), 200 # Return 200 OK, but status indicates error

    except Exception as e:
        logger.error(f"Error checking status for {app_name}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"An unexpected error occurred while checking {app_name} status."}), 500

# Add other common routes as needed (e.g., system info, logs?)
