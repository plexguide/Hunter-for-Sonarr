import os
import time
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('huntarr')

def main():
    logger.info("Huntarr Sonarr started")
    logger.info("Using configuration values from environment variables")
    
    # Access environment variables
    api_key = os.environ.get('API_KEY', 'missing')
    api_url = os.environ.get('API_URL', 'missing')
    
    if api_key == 'your-api-key' or api_url == 'http://your-sonarr-address:8989':
        logger.warning("Please update API_KEY and API_URL in your docker-compose.yml")
    
    logger.info(f"API URL: {api_url}")
    logger.info("Huntarr is ready!")
    
    # Keep container running
    try:
        while True:
            time.sleep(60)
            logger.debug("Huntarr still running...")
    except KeyboardInterrupt:
        logger.info("Shutting down Huntarr...")

if __name__ == "__main__":
    main()