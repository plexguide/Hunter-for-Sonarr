#!/usr/bin/env python3
"""
Plex authentication routes for Huntarr
Handles Plex OAuth PIN-based authentication flow
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from src.primary.auth import (
    create_plex_pin, check_plex_pin, verify_plex_token, create_user_with_plex,
    link_plex_account, verify_plex_user, create_session, user_exists,
    SESSION_COOKIE_NAME, verify_user, unlink_plex_from_user
)
from src.primary.utils.logger import logger
import time

# Create blueprint for Plex authentication routes
plex_auth_bp = Blueprint('plex_auth', __name__)

@plex_auth_bp.route('/api/auth/plex/pin', methods=['POST'])
def create_pin():
    """Create a new Plex PIN for authentication"""
    try:
        pin_data = create_plex_pin()
        if pin_data:
            return jsonify({
                'success': True,
                'pin_id': pin_data['id'],
                'auth_url': pin_data['auth_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create Plex PIN'
            }), 500
    except Exception as e:
        logger.error(f"Error creating Plex PIN: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@plex_auth_bp.route('/api/auth/plex/check/<int:pin_id>', methods=['GET'])
def check_pin(pin_id):
    """Check if a Plex PIN has been claimed"""
    try:
        token = check_plex_pin(pin_id)
        if token:
            # Verify the token and get user data
            plex_user_data = verify_plex_token(token)
            if plex_user_data:
                return jsonify({
                    'success': True,
                    'claimed': True,
                    'token': token,
                    'user_data': {
                        'username': plex_user_data.get('username'),
                        'email': plex_user_data.get('email'),
                        'id': plex_user_data.get('id')
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid Plex token'
                }), 400
        else:
            return jsonify({
                'success': True,
                'claimed': False
            })
    except Exception as e:
        logger.error(f"Error checking Plex PIN {pin_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@plex_auth_bp.route('/api/auth/plex/login', methods=['POST'])
def plex_login():
    """Login with Plex token (for first-time setup or Plex-only users)"""
    try:
        data = request.json
        plex_token = data.get('token')
        
        if not plex_token:
            return jsonify({
                'success': False,
                'error': 'Plex token is required'
            }), 400
        
        # Verify Plex token
        success, plex_user_data = verify_plex_user(plex_token)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Invalid Plex token'
            }), 401
        
        # Check if a local user already exists
        if not user_exists():
            # Create new Plex-only user
            if create_user_with_plex(plex_token, plex_user_data):
                # Create session
                session_id = create_session(plex_user_data.get('username'))
                
                response = jsonify({
                    'success': True,
                    'message': 'Plex user created and logged in successfully',
                    'auth_type': 'plex'
                })
                session[SESSION_COOKIE_NAME] = session_id  # Store in Flask session
                response.set_cookie(SESSION_COOKIE_NAME, session_id, 
                                  max_age=60*60*24*7, httponly=True, secure=False)
                return response
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to create Plex user'
                }), 500
        else:
            # User exists - this means they want to login with existing Plex-linked account
            from src.primary.auth import get_user_data
            user_data = get_user_data()
            
            if user_data.get('auth_type') == 'plex' or user_data.get('plex_linked'):
                # Check if this is the same Plex user
                if user_data.get('plex_user_id') == plex_user_data.get('id'):
                    # Update token in case it changed
                    user_data['plex_token'] = plex_token
                    from src.primary.auth import save_user_data
                    save_user_data(user_data)
                    
                    # Create session
                    username = user_data.get('plex_username') or user_data.get('username', 'unknown')
                    session_id = create_session(username)
                    
                    response = jsonify({
                        'success': True,
                        'message': 'Logged in with Plex successfully',
                        'auth_type': 'plex'
                    })
                    session[SESSION_COOKIE_NAME] = session_id  # Store in Flask session
                    response.set_cookie(SESSION_COOKIE_NAME, session_id, 
                                      max_age=60*60*24*7, httponly=True, secure=False)
                    return response
                else:
                    return jsonify({
                        'success': False,
                        'error': 'This Plex account is not linked to this Huntarr instance'
                    }), 403
            else:
                return jsonify({
                    'success': False,
                    'error': 'Local user exists but Plex account is not linked. Please use account linking.'
                }), 409
                
    except Exception as e:
        logger.error(f"Error during Plex login: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@plex_auth_bp.route('/api/auth/plex/link', methods=['POST'])
def link_account():
    """Link Plex account to existing local user"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        plex_token = data.get('token')
        
        if not all([username, password, plex_token]):
            return jsonify({
                'success': False,
                'error': 'Username, password, and Plex token are required'
            }), 400
        
        # Verify Plex token
        success, plex_user_data = verify_plex_user(plex_token)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Invalid Plex token'
            }), 401
        
        # Link accounts
        if link_plex_account(username, password, plex_token, plex_user_data):
            return jsonify({
                'success': True,
                'message': 'Plex account linked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to link Plex account. Please check your credentials.'
            }), 400
            
    except Exception as e:
        logger.error(f"Error linking Plex account: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@plex_auth_bp.route('/api/auth/plex/unlink', methods=['POST'])
def unlink_plex_account():
    """Unlink Plex account from local user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Verify the local user credentials first
        is_valid, requires_2fa = verify_user(username, password)
        if not is_valid:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Remove Plex data from user credentials
        if unlink_plex_from_user(username):
            return jsonify({'success': True, 'message': 'Plex account unlinked successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to unlink Plex account'}), 500
            
    except Exception as e:
        logger.error(f"Error unlinking Plex account: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@plex_auth_bp.route('/api/auth/plex/status', methods=['GET'])
def plex_status():
    """Get Plex authentication status for current user"""
    try:
        from src.primary.auth import get_user_data
        user_data = get_user_data()
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'No user found'
            }), 404
        
        plex_linked = user_data.get('plex_linked', False)
        auth_type = user_data.get('auth_type', 'local')
        
        response_data = {
            'success': True,
            'plex_linked': plex_linked,
            'auth_type': auth_type
        }
        
        if plex_linked or auth_type == 'plex':
            response_data.update({
                'plex_username': user_data.get('plex_username'),
                'plex_email': user_data.get('plex_email'),
                'plex_linked_at': user_data.get('plex_linked_at')
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting Plex status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@plex_auth_bp.route('/auth/plex/callback')
def plex_callback():
    """Handle Plex authentication callback (redirect back to app)"""
    # This is just a landing page that will trigger the frontend to check the PIN
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plex Authentication - Huntarr</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #1a1d24; color: #fff; }
            .container { max-width: 500px; margin: 0 auto; }
            .logo { width: 100px; height: 100px; margin: 20px auto; }
            .success { color: #28a745; }
            .spinner { animation: spin 1s linear infinite; display: inline-block; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🎬</div>
            <h2>Plex Authentication Successful!</h2>
            <p class="success">✓ You have successfully authenticated with Plex.</p>
            <p>You can now close this window and return to Huntarr.</p>
            <div class="spinner">⟳</div>
            <p><small>Redirecting automatically...</small></p>
        </div>
        <script>
            // Close the window after a brief delay
            setTimeout(() => {
                window.close();
            }, 3000);
        </script>
    </body>
    </html>
    '''
