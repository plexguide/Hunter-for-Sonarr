#!/usr/bin/env python3
"""
Authentication module for Huntarr
Handles user creation, verification, and session management
Including two-factor authentication
"""

import os
import json
import hashlib
import secrets
import time
import pathlib
import base64
import io
import qrcode
import pyotp # Ensure pyotp is imported
import re # Import the re module for regex
from typing import Dict, Any, Optional, Tuple
from flask import request, redirect, url_for, session
from .utils.logger import logger # Ensure logger is imported

# User directory setup
# Use the centralized path configuration
from src.primary.utils.config_paths import USER_DIR

# User directory is already created by config_paths module
USER_FILE = USER_DIR / "credentials.json"

# Session settings
SESSION_EXPIRY = 60 * 60 * 24 * 7  # 1 week in seconds
SESSION_COOKIE_NAME = "huntarr_session"

# Store active sessions
active_sessions = {}

# --- Add Helper functions for user data ---
def get_user_data() -> Dict[str, Any]:
    """Load user data from the credentials file."""
    if not USER_FILE.exists():
        logger.warning(f"Attempted to get user data, but file not found: {USER_FILE}")
        return {}
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from user file: {USER_FILE}")
        return {}
    except Exception as e:
        logger.error(f"Error reading user file {USER_FILE}: {e}", exc_info=True)
        return {}

def save_user_data(user_data: Dict[str, Any]) -> bool:
    """Save user data to the credentials file."""
    try:
        logger.debug(f"Attempting to save user data to: {USER_FILE}")
        # Ensure directory exists (though it should from startup)
        USER_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(USER_FILE, 'w') as f:
            json.dump(user_data, f, indent=4) # Add indent for readability
        
        # Set permissions after writing
        try:
            os.chmod(USER_FILE, 0o644)
            logger.debug(f"Set permissions 0o644 on {USER_FILE}")
        except Exception as e_perm:
            logger.warning(f"Could not set permissions on file {USER_FILE}: {e_perm}")
            
        logger.info(f"User data saved successfully to {USER_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving user file {USER_FILE}: {e}", exc_info=True)
        return False
# --- End Helper functions ---

def hash_password(password: str) -> str:
    """Hash a password for storage"""
    # Use SHA-256 with a salt
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pw_hash}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pw_hash = stored_password.split(':', 1)
        verify_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
        return secrets.compare_digest(verify_hash, pw_hash)
    except Exception as e:
        logger.error(f"Error verifying password hash: {e}", exc_info=True)
        return False

def hash_username(username: str) -> str:
    """Create a normalized hash of the username"""
    # Convert to lowercase and hash
    return hashlib.sha256(username.lower().encode()).hexdigest()

def validate_password_strength(password: str) -> Optional[str]:
    """Validate password strength based on defined criteria.

    Args:
        password: The password string to validate.

    Returns:
        An error message string if validation fails, None otherwise.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    
    # If check passes
    return None

def user_exists() -> bool:
    """Check if a user has been created"""
    return USER_FILE.exists() and os.path.getsize(USER_FILE) > 0

def create_user(username: str, password: str) -> bool:
    """Create a new user"""
    if not username or not password:
        logger.error("Attempted to create user with empty username or password")
        return False
        
    # Ensure user directory exists with proper permissions
    logger.info(f"Ensuring user directory exists: {USER_DIR}")
    USER_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # Set appropriate permissions if not running as root
        logger.info(f"Setting permissions on directory: {USER_DIR}")
        os.chmod(USER_DIR, 0o755)
    except Exception as e:
        logger.warning(f"Could not set permissions on directory {USER_DIR}: {e}")
        
    # Hash the username and password
    username_hash = hash_username(username)
    password_hash = hash_password(password)
    
    # Store the credentials
    user_data = {
        "username": username_hash,
        "password": password_hash,
        "created_at": time.time(),
        "2fa_enabled": False,
        "2fa_secret": None
    }
    
    try:
        logger.info(f"Writing user file: {USER_FILE}")
        with open(USER_FILE, 'w') as f:
            json.dump(user_data, f)
        # Set appropriate permissions on the file
        try:
            logger.info(f"Setting permissions on file: {USER_FILE}")
            os.chmod(USER_FILE, 0o644)
        except Exception as e:
            logger.warning(f"Could not set permissions on file {USER_FILE}: {e}")
        logger.info("User creation successful")
        return True
    except Exception as e:
        logger.error(f"Error creating user file {USER_FILE}: {e}", exc_info=True)
        return False

def verify_user(username: str, password: str, otp_code: str = None) -> Tuple[bool, bool]:
    """
    Verify user credentials
    
    Returns:
        Tuple[bool, bool]: (auth_success, needs_2fa)
    """
    if not user_exists():
        logger.warning("Login attempt failed: User does not exist.")
        return False, False
        
    try:
        with open(USER_FILE, 'r') as f:
            user_data = json.load(f)
            
        # Hash the provided username
        username_hash = hash_username(username)
        
        # Compare username and verify password
        if user_data.get("username") == username_hash:
            if verify_password(user_data.get("password", ""), password):
                # Check if 2FA is enabled
                two_fa_enabled = user_data.get("2fa_enabled", False)
                logger.debug(f"2FA enabled for user '{username}': {two_fa_enabled}")
                logger.debug(f"2FA secret present: {bool(user_data.get('2fa_secret'))}")
                logger.debug(f"OTP code provided: {bool(otp_code)}")
                
                if two_fa_enabled:
                    # If 2FA code was provided, verify it
                    if otp_code:
                        totp = pyotp.TOTP(user_data.get("2fa_secret"))
                        valid_code = totp.verify(otp_code)
                        logger.debug(f"OTP code validation result: {valid_code}")
                        if valid_code:
                            logger.info(f"User '{username}' authenticated successfully with 2FA.")
                            return True, False
                        else:
                            logger.warning(f"Login attempt failed for user '{username}': Invalid 2FA code.")
                            return False, True
                    else:
                        # No OTP code provided but 2FA is enabled
                        logger.warning(f"Login attempt failed for user '{username}': 2FA code required but not provided.")
                        logger.debug("Returning needs_2fa=True to trigger 2FA input display")
                        return False, True
                else:
                    # 2FA not enabled, password is correct
                    logger.info(f"User '{username}' authenticated successfully (no 2FA).")
                    return True, False
            else:
                logger.warning(f"Login attempt failed for user '{username}': Invalid password.")
                return False, False
    except Exception as e:
        logger.error(f"Error during user verification for '{username}': {e}", exc_info=True)
    
    logger.warning(f"Login attempt failed for user '{username}': Username not found or other error.")
    return False, False

def create_session(username: str) -> str:
    """Create a new session for an authenticated user"""
    session_id = secrets.token_hex(32)
    # Store the actual username, not the hash
    
    # Store session data
    active_sessions[session_id] = {
        "username": username, # Store actual username
        "created_at": time.time(),
        "expires_at": time.time() + SESSION_EXPIRY
    }
    
    return session_id

def verify_session(session_id: str) -> bool:
    """Verify if a session is valid"""
    if not session_id or session_id not in active_sessions:
        return False
        
    session_data = active_sessions[session_id]
    
    # Check if session has expired
    if session_data.get("expires_at", 0) < time.time():
        # Clean up expired session
        del active_sessions[session_id]
        return False
        
    # Extend session expiry
    active_sessions[session_id]["expires_at"] = time.time() + SESSION_EXPIRY
    return True

def get_username_from_session(session_id: str) -> Optional[str]:
    """Get the username from a session"""
    if not session_id or session_id not in active_sessions:
        return None
    
    # Return the stored username
    return active_sessions[session_id].get("username")

def authenticate_request():
    """Flask route decorator to check if user is authenticated"""

    # Skip authentication for static files and the login/setup pages
    static_path = "/static/"
    login_path = "/login"
    api_login_path = "/api/login"
    setup_path = "/setup"
    api_setup_path = "/api/setup"
    favicon_path = "/favicon.ico"
    health_check_path = "/api/health"
    ping_path = "/ping"

    # Skip authentication for static files, setup pages, health check path, and ping
    if request.path.startswith((static_path, setup_path, api_setup_path)) or request.path in (favicon_path, health_check_path, ping_path):
        return None
    
    # If no user exists, redirect to setup
    if not user_exists():
        return redirect(url_for("common.setup"))
    
    # Skip authentication for login pages
    if request.path.startswith((login_path, api_login_path)):
        return None
    
    # Load general settings
    local_access_bypass = False
    proxy_auth_bypass = False
    try:
        # Force reload settings from disk to ensure we have the latest
        from src.primary.settings_manager import load_settings
        from src.primary import settings_manager
        
        # Ensure we're getting fresh settings by clearing any cache
        if hasattr(settings_manager, 'settings_cache'):
            settings_manager.settings_cache = {}
            
        settings = load_settings("general")  # Specify 'general' as the app_type
        general_settings = settings
        local_access_bypass = general_settings.get("local_access_bypass", False)
        proxy_auth_bypass = general_settings.get("proxy_auth_bypass", False)
        logger.debug(f"Local access bypass setting: {local_access_bypass}")
        logger.debug(f"Proxy auth bypass setting: {proxy_auth_bypass}")
        
        # Debug print all general settings
        logger.debug(f"All general settings: {general_settings}")
    except Exception as e:
        logger.error(f"Error loading authentication bypass settings: {e}", exc_info=True)
    
    # Check if proxy auth bypass is enabled - this completely disables authentication
    # Note: This has highest priority and is checked first (matching the "No Login Mode" in the UI)
    if proxy_auth_bypass:
        logger.info("Proxy authentication bypass is ENABLED (No Login Mode) - Authentication bypassed!")
        return None
    
    remote_addr = request.remote_addr
    logger.debug(f"Request IP address: {remote_addr}")
    
    if local_access_bypass:
        # Common local network IP ranges
        local_networks = [
            '127.0.0.1',      # localhost
            '::1',            # localhost IPv6
            '10.',            # 10.0.0.0/8
            '172.16.',        # 172.16.0.0/12
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.',
            '192.168.'        # 192.168.0.0/16
        ]
        is_local = False
        
        # Check if request is coming through a proxy
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            logger.debug(f"X-Forwarded-For header detected: {forwarded_for}")
            # Take the first IP in the chain which is typically the client's real IP
            possible_client_ip = forwarded_for.split(',')[0].strip()
            logger.debug(f"Checking if forwarded IP {possible_client_ip} is local")
            
            # Check if this forwarded IP is a local network IP
            for network in local_networks:
                if possible_client_ip == network or (network.endswith('.') and possible_client_ip.startswith(network)):
                    is_local = True
                    logger.debug(f"Forwarded IP {possible_client_ip} is a local network IP (matches {network})")
                    break
        
        # Check if direct remote_addr is a local network IP if not already determined
        if not is_local:
            for network in local_networks:
                if remote_addr == network or (network.endswith('.') and remote_addr.startswith(network)):
                    is_local = True
                    logger.debug(f"Direct IP {remote_addr} is a local network IP (matches {network})")
                    break
                    
        if is_local:
            logger.debug(f"Local network access from {remote_addr} - Authentication bypassed! (Local Bypass Mode)")
            return None
        else:
            logger.warning(f"Access from {remote_addr} is not recognized as local network - Authentication required")
    else:
        logger.debug("Local Bypass Mode is DISABLED - Authentication required")
    
    # Check for valid session
    session_id = session.get(SESSION_COOKIE_NAME)
    if session_id and verify_session(session_id):
        return None
    
    # No valid session, redirect to login
    api_path = "/api/"
    if not request.path.startswith(api_path):
        return redirect(url_for("common.login_route"))
    
    # For API calls, return 401 Unauthorized
    if request.path.startswith("/api/"):
        return {"error": "Unauthorized"}, 401
    
    return None

def logout(session_id: str):
    """Log out the current user by invalidating their session"""
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    # Clear the session cookie in Flask context (if available, otherwise handled by route)
    # session.pop(SESSION_COOKIE_NAME, None) # This might be better handled solely in the route

def is_2fa_enabled(username):
    """Check if 2FA is enabled for a user."""
    user_data = get_user_data()
    return user_data.get('2fa_enabled', False)

def generate_2fa_secret(username: str) -> Tuple[str, str]:
    """
    Generate a new 2FA secret and QR code
    
    Returns:
        Tuple[str, str]: (secret, qr_code_data_uri)
    """
    # Generate a random secret
    secret = pyotp.random_base32()
    
    # Create a TOTP object
    totp = pyotp.TOTP(secret)
    
    # Get the provisioning URI - Use the actual username here
    uri = totp.provisioning_uri(name=username, issuer_name="Huntarr")
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    try:
        img = qr.make_image(fill_color="black", back_color="white")
    
        # Convert to base64 string
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
    
        # Store the secret temporarily associated with the user
        user_data = get_user_data()
        user_data["temp_2fa_secret"] = secret
        if save_user_data(user_data):
            logger.info(f"Generated temporary 2FA secret for user '{username}'.")
            return secret, f"data:image/png;base64,{img_str}"
        else:
            logger.error(f"Failed to save temporary 2FA secret for user '{username}'.")
            raise Exception("Failed to save user data with temporary 2FA secret.")
    
    except Exception as e:
        logger.error(f"Error generating 2FA QR code for user '{username}': {e}", exc_info=True)
        raise

def verify_2fa_code(username: str, code: str, enable_on_verify: bool = False) -> bool:
    """Verify a 2FA code against the temporary secret"""
    user_data = get_user_data()
    temp_secret = user_data.get("temp_2fa_secret")
    
    if not temp_secret:
        logger.warning(f"2FA verification attempt for '{username}' failed: No temporary secret found.")
        return False
    
    totp = pyotp.TOTP(temp_secret)
    if totp.verify(code):
        logger.info(f"2FA code verified successfully for user '{username}'.")
        if enable_on_verify:
            user_data["2fa_enabled"] = True
            user_data["2fa_secret"] = temp_secret
            user_data.pop("temp_2fa_secret", None)
            if save_user_data(user_data):
                logger.info(f"2FA enabled permanently for user '{username}'.")
            else:
                logger.error(f"Failed to save user data after enabling 2FA for '{username}'.")
                return False
        return True
    else:
        logger.warning(f"Invalid 2FA code provided by user '{username}'.")
        return False

def disable_2fa(password: str) -> bool:
    """Disable 2FA for the current user (using only password - kept for potential other uses)"""
    user_data = get_user_data()
    
    # Verify password
    if verify_password(user_data.get("password", ""), password):
        user_data["2fa_enabled"] = False
        user_data["2fa_secret"] = None
        if save_user_data(user_data):
            logger.info("2FA disabled successfully (password only).")
            return True
        else:
            logger.error("Failed to save user data after disabling 2FA (password only).")
            return False
    else:
        logger.warning("Failed to disable 2FA (password only): Invalid password provided.")
        return False

def disable_2fa_with_password_and_otp(username: str, password: str, otp_code: str) -> bool:
    """Disable 2FA for the specified user, requiring both password and OTP code."""
    user_data = get_user_data() # Assuming this gets data for the logged-in user implicitly
    
    # 1. Verify Password
    if not verify_password(user_data.get("password", ""), password):
        logger.warning(f"Failed to disable 2FA for '{username}': Invalid password provided.")
        return False
        
    # 2. Verify OTP Code against permanent secret
    perm_secret = user_data.get("2fa_secret")
    if not user_data.get("2fa_enabled") or not perm_secret:
        logger.error(f"Failed to disable 2FA for '{username}': 2FA is not enabled or secret missing.")
        # Should ideally not happen if called from the correct UI state, but good to check
        return False 
        
    totp = pyotp.TOTP(perm_secret)
    if not totp.verify(otp_code):
        logger.warning(f"Failed to disable 2FA for '{username}': Invalid OTP code provided.")
        return False
        
    # 3. Both verified, proceed to disable
    user_data["2fa_enabled"] = False
    user_data["2fa_secret"] = None
    if save_user_data(user_data):
        logger.info(f"2FA disabled successfully for '{username}' after verifying password and OTP.")
        return True
    else:
        logger.error(f"Failed to save user data after disabling 2FA for '{username}'.")
        return False

def change_username(current_username: str, new_username: str, password: str) -> bool:
    """Change the username for the current user"""
    user_data = get_user_data()
    
    # Verify current username and password
    current_username_hash = hash_username(current_username)
    if user_data.get("username") != current_username_hash:
        logger.warning(f"Username change failed: Current username '{current_username}' does not match stored hash.")
        return False
    
    if not verify_password(user_data.get("password", ""), password):
        logger.warning(f"Username change failed for '{current_username}': Invalid password provided.")
        return False
    
    # Update username
    user_data["username"] = hash_username(new_username)
    if save_user_data(user_data):
        logger.info(f"Username changed successfully from '{current_username}' to '{new_username}'.")
        return True
    else:
        logger.error(f"Failed to save user data after changing username for '{current_username}'.")
        return False

def change_password(current_password: str, new_password: str) -> bool:
    """Change the password for the current user"""
    user_data = get_user_data()
    
    # Verify current password
    if not verify_password(user_data.get("password", ""), current_password):
        logger.warning("Password change failed: Invalid current password provided.")
        return False
    
    # Update password
    user_data["password"] = hash_password(new_password)
    if save_user_data(user_data):
        logger.info("Password changed successfully.")
        return True
    else:
        logger.error("Failed to save user data after changing password.")
        return False

def get_app_url_and_key(app_type: str) -> Tuple[str, str]:
    """
    Get the API URL and API key for a specific app type
    
    Args:
        app_type: The app type (sonarr, radarr, lidarr, readarr)
    
    Returns:
        Tuple[str, str]: (api_url, api_key)
    """
    from primary import keys_manager
    return keys_manager.get_api_keys(app_type)