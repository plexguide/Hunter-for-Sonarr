from flask import Blueprint, request

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # ...existing code...
    
    # Remove or comment out any logging of the web interface URL here
    # logger.info(f"Web interface available at http://{request.host}")
    
    # ...existing code...