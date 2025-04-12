from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ...existing code...

# Standard routes for the main UI
@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/user')
def user_page():
    """Serve the user settings page"""
    return render_template('user.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        # Handle form submission via AJAX
        if request.content_type and 'application/json' in request.content_type:
            data = request.json
            username = data.get('username')
            password = data.get('password')
        else:
            # Handle regular form submission
            username = request.form.get('username')
            password = request.form.get('password')
            
        # Process login - this is where you'd check credentials
        # This is a placeholder, replace with actual authentication
        if username == 'admin' and password == 'admin':
            # Successful login
            return jsonify({'success': True, 'redirect': '/'})
        else:
            # Failed login
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    # GET request - display login page
    return render_template('login.html')

# ...existing code...

if __name__ == '__main__':
    app.run(debug=True)