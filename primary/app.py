import logging

class WebAddressFilter(logging.Filter):
    """Filter out web interface availability messages"""
    def filter(self, record):
        if "Web interface available at http://" in record.getMessage():
            return False
        return True

# Configure logging
def configure_logging():
    logging.basicConfig(level=logging.INFO)
    
    # Add filter to remove web interface URL logs
    for handler in logging.root.handlers:
        handler.addFilter(WebAddressFilter())
    
    logging.info("Logging is configured.")

if __name__ == "__main__":
    configure_logging()
    logging.info("Web interface available at http://localhost:8080")