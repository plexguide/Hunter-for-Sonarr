# Windows patch for config paths
import os
import sys
import pathlib
import logging
import shutil

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
            # Find default configs directory based on environment
            default_configs_dir = None
            
            if getattr(sys, 'frozen', False):
                # For frozen app
                default_configs_dir = os.path.join(os.path.dirname(sys.executable), 
                                                  'src', 'primary', 'default_configs')
                if not os.path.exists(default_configs_dir):
                    # Try alternate location
                    default_configs_dir = os.path.join(os.path.dirname(sys.executable), 
                                                      'default_configs')
            else:
                # For running as script
                default_configs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                  'src', 'primary', 'default_configs')
            
            if default_configs_dir and os.path.exists(default_configs_dir):
                logger.info(f"Copying default configs from {default_configs_dir}")
                for config_file in os.listdir(default_configs_dir):
                    if config_file.endswith('.json'):
                        src_file = os.path.join(default_configs_dir, config_file)
                        dst_file = os.path.join(settings_dir, config_file)
                        # Only copy if not exists
                        if not os.path.exists(dst_file):
                            shutil.copy2(src_file, dst_file)
                            logger.info(f"Copied default config: {config_file}")
            else:
                logger.warning(f"Default configs directory not found: {default_configs_dir}")
        except Exception as e:
            logger.error(f"Failed to copy default configs: {str(e)}")
    
    return config_dir

# Helper function to get Windows log directory
def get_logs_dir():
    """Get path to logs directory for Windows"""
    config_dir = get_config_dir()
    logs_dir = os.path.join(config_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

# Helper function to resolve Windows-compatible paths
def get_windows_path(original_path):
    """
    Convert Docker/Linux paths to Windows paths.
    This helps handle paths that might be hardcoded as /config/...
    """
    if original_path.startswith('/config/'):
        config_dir = get_config_dir()
        windows_path = os.path.join(config_dir, original_path[8:])
        return windows_path
    return original_path
