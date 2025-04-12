from flask import Flask, render_template

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

# ...existing code...

if __name__ == '__main__':
    app.run(debug=True)