import logging
import os

log_dir = r"/config/log"
os.makedirs(log_dir, exist_ok=True)
format = '%(asctime)s - %(levelname)s - %(message)s'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=format,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Huntarr')


# File Handler (all logs)
file_handler = logging.FileHandler(os.path.join(log_dir, "huntarr.log"))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(format)
logger.addHandler(file_handler)
