import logging

class SensitiveInfoFilter(logging.Filter):
    """Filter out sensitive information from logs"""
    def filter(self, record):
        message = record.getMessage()
        # Filter out web interface URLs
        if "Web interface available at http://" in message:
            return False
        # Add more filters as needed
        return True

def configure_logging(level=logging.INFO):
    """Configure logging with filters for sensitive information"""
    # Basic config
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add the filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(SensitiveInfoFilter())
    
    # Individual loggers can also be configured here
    logger = logging.getLogger('huntarr')
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.addFilter(SensitiveInfoFilter())
    
    return logger
