# ...existing code...

def start_server(host='0.0.0.0', port=9876, debug=False):
    """Start the web server"""
    # ...existing code...
    
    # Change this line:
    # logger.info(f"Web interface available at http://{host}:{port}")
    
    # To this (more discreet version):
    logger.info(f"Server started on port {port}")
    
    # ...existing code...

# ...existing code...