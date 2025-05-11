# Windows patch for config paths
import os
import sys
import pathlib
import logging

# Setup a logger for this module
logger = logging.getLogger("windows_config")

# Patch function to ensure config path works on Windows
def get_config_dir():
    """
    Get the appropriate config directory for Windows.
    When running as an executable, this will be next to the exe.
    When running as a script, this will be in the project root.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_dir = os.path.dirname(sys.executable)
        logger.info(f"Running as frozen application from {base_dir}")
    else:
        # Running as script
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        logger.info(f"Running as script from {base_dir}")
    
    config_dir = os.path.join(base_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)
    logger.info(f"Using config directory: {config_dir}")
    return config_dir
    
# Create directories for config
def ensure_config_dirs():
    """
    Ensure all required config directories exist.
    Returns the base config directory path.
    """
    config_dir = get_config_dir()
    data_dir = os.path.join(config_dir, 'data')
    logs_dir = os.path.join(config_dir, 'logs')
    settings_dir = os.path.join(config_dir, 'settings')
    
    # Create each directory
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(settings_dir, exist_ok=True)
    
    # Copy default configs if settings directory is empty
    if not os.listdir(settings_dir):
        try:
            # Import here to avoid circular imports
            from src.primary import settings_manager
            default_configs_dir = settings_manager.DEFAULT_CONFIGS_DIR
            
            if os.path.exists(default_configs_dir):
                for config_file in os.listdir(default_configs_dir):
                    if config_file.endswith('.json'):
                        src_file = os.path.join(default_configs_dir, config_file)
                        dst_file = os.path.join(settings_dir, config_file)
                        # Only copy if not exists
                        if not os.path.exists(dst_file):
                            import shutil
                            shutil.copy2(src_file, dst_file)
                            logger.info(f"Copied default config: {config_file}")
        except Exception as e:
            logger.error(f"Failed to copy default configs: {str(e)}")
    
    return config_dir
