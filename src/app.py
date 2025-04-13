from flask import Flask, render_template, request, jsonify, session, redirect
from primary.auth import verify_user, create_session, authenticate_request, SESSION_COOKIE_NAME, user_exists
import os

# Configure Flask to use templates and static files from the frontend folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'your_secret_key'  # Should be a secure random value in production

# Standard routes for the main UI
@app.route('/')
def index():
    """Serve the main UI"""
    # Check authentication
    auth_result = authenticate_request()
    if auth_result is not None:
        return auth_result
    return render_template('index.html')

@app.route('/user')
def user_page():
    """Serve the user settings page"""
    # Check authentication
    auth_result = authenticate_request()
    if auth_result is not None:
        return auth_result
    return render_template('user.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If no user exists yet, redirect to setup
    if not user_exists():
        return redirect('/setup')
        
    if request.method == 'POST':
        # Handle form submission via AJAX
        if request.content_type and 'application/json' in request.content_type:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            otp_code = data.get('twoFactorCode')
        else:
            # Handle regular form submission
            username = request.form.get('username')
            password = request.form.get('password')
            otp_code = request.form.get('twoFactorCode')
            
        # Use the auth module to verify credentials
        auth_success, needs_2fa = verify_user(username, password, otp_code)
        
        if auth_success:
            # Create a new session and set the cookie
            session_id = create_session(username)
            session[SESSION_COOKIE_NAME] = session_id
            return jsonify({'success': True, 'redirect': '/'})
        elif needs_2fa:
            # User authenticated but 2FA is required
            return jsonify({'success': False, 'requires2fa': True, 'message': 'Please enter your 2FA code'})
        else:
            # Failed login
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    # GET request - display login page
    return render_template('login.html')

@app.route('/setup', methods=['GET'])
def setup():
    """Setup page for initial user creation"""
    # Only show setup if no user exists
    if user_exists():
        return redirect('/')
    return render_template('setup.html')

if __name__ == '__main__':
    app.run(debug=True)