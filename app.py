from flask import Flask, render_template

app = Flask(__name__)

# ...existing code...

# Add routes for new UI
@app.route('/new')
def new_ui():
    """Serve the new UI"""
    return render_template('new-index.html')

@app.route('/user/new')
def new_user_page():
    """Serve the new user settings page"""
    return render_template('new-user.html')

# ...existing code...

if __name__ == '__main__':
    app.run(debug=True)