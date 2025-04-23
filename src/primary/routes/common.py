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
        try: # Add try block to catch potential errors during user creation
            data = request.json
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({"success": False, "error": "Username and password are required"}), 400

            if create_user(username, password):
                # Automatically log in the user after setup
                session_token = create_session(username)
                # Explicitly set username in Flask session
                session['username'] = username 
                session[SESSION_COOKIE_NAME] = session_token
                response = jsonify({"success": True})
                # Set cookie in the response
                response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, samesite='Lax')
                return response
            else:
                # create_user itself failed, but didn't raise an exception
                return jsonify({"success": False, "error": "Failed to create user (internal reason)"}), 500
        except Exception as e:
            # Catch any unexpected exception during the process
            logger.error(f"Unexpected error during setup POST: {e}", exc_info=True)
            return jsonify({"success": False, "error": f"An unexpected server error occurred: {e}"}), 500
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
        logger.warning("2FA setup attempt failed: No username in session.") # Add logging
        return jsonify({"error": "Not authenticated"}), 401

    # Pass username to generate_2fa_secret
    secret, uri = generate_2fa_secret(username)
    
    # Generate QR code
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    logger.info(f"Generated 2FA setup for user: {username}") # Add logging
    return jsonify({"success": True, "secret": secret, "qr_code": qr_code_base64})

@common_bp.route('/api/user/2fa/verify', methods=['POST'])
def verify_2fa():
    username = session.get('username')
    if not username:
        logger.warning("2FA verify attempt failed: No username in session.") # Add logging
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    otp_code = data.get('otp_code')

    if not otp_code:
        return jsonify({"success": False, "error": "OTP code is required"}), 400

    # Pass username to verify_2fa_code
    if verify_2fa_code(username, otp_code, enable_on_verify=True):
        logger.info(f"Successfully verified and enabled 2FA for user: {username}") # Add logging
        return jsonify({"success": True})
    else:
        logger.warning(f"Invalid OTP code provided for user: {username}") # Add logging
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

# REMOVED DUPLICATE BLUEPRINT DEFINITION AND CONFLICTING ROUTES BELOW THIS LINE
