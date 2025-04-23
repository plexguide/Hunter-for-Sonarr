from flask import Flask, render_template, request, jsonify, session, redirect
from src.primary.auth import verify_user, create_session, authenticate_request, SESSION_COOKIE_NAME, user_exists
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

@app.route('/setup', methods=['GET'])
def setup():
    """Setup page for initial user creation"""
    # Only show setup if no user exists
    if user_exists():
        return redirect('/')
    return render_template('setup.html')

if __name__ == '__main__':
    app.run(debug=True)