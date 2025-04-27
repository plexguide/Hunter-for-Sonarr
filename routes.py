from flask import Flask, render_template, request, redirect, send_file

app = Flask(__name__)

import os
import json

def get_ui_preference():
    """Determine which UI to use based on config and user preference"""
    # Check if ui_settings.json exists
    config_file = os.path.join(os.path.dirname(__file__), 'config/ui_settings.json')
    
    use_new_ui = False
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)
                use_new_ui = settings.get('use_new_ui', False)
        except Exception as e:
            print(f"Error loading UI settings: {e}")
    
    # Allow URL parameter to override
    ui_param = request.args.get('ui', None)
    if ui_param == 'new':
        use_new_ui = True
    elif ui_param == 'classic':
        use_new_ui = False
    
    return use_new_ui

@app.route('/')
def index():
    """Root route with UI switching capability"""
    if get_ui_preference():
        return redirect('/new')
    else:
        return render_template('index.html')

@app.route('/user')
def user_page():
    """User settings page with UI switching capability"""
    return render_template('user.html')

@app.route('/user/new')
def user_new_page():
    """User settings page for new UI"""
    return render_template('user.html')

@app.route('/version.txt')
def version_txt():
    """Serve version.txt file directly"""
    version_path = os.path.join(os.path.dirname(__file__), 'version.txt')
    print(f"Serving version.txt from path: {version_path}")  # Debug log
    try:
        return send_file(version_path, mimetype='text/plain')
    except Exception as e:
        print(f"Error serving version.txt: {e}")  # Log any errors
        return str(e), 500  # Return error message and 500 status code

if __name__ == '__main__':
    app.run(debug=True)