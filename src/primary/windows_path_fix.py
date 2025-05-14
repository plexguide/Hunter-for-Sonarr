"""
Windows path fix for Huntarr
Ensures that config paths work correctly on Windows systems
"""

import os
import sys
import logging
import traceback
from pathlib import Path
import platform

def setup_windows_paths():
    """
    Setup Windows-specific paths for Huntarr
    This function ensures that the config directory is properly created and accessible
    on Windows, resolving potential 500 errors related to path issues.
    """
    # Set up basic logging to stdout in case file logging isn't working yet
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("WindowsPathFix")
    
    try:
        # When running as installed app or PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            app_path = os.path.dirname(sys.executable)
            logger.info(f"Running as PyInstaller bundle from: {app_path}")
            
            # Alternative paths to try if the default doesn't work
            alt_paths = [
                app_path,
                os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Huntarr'),
                os.path.join(os.environ.get('LOCALAPPDATA', 'C:\\Users\\' + os.environ.get('USERNAME', 'Default') + '\\AppData\\Local'), 'Huntarr')
            ]
        else:
            # Running as script
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logger.info(f"Running as script from: {app_path}")
            alt_paths = [app_path]
        
        # Try the primary path first
        config_dir = os.path.join(app_path, 'config')
        
        # Try to create the config directory and test if it's writable
        success = False
        error_messages = []
        
        for path in alt_paths:
            try:
                config_dir = os.path.join(path, 'config')
                logger.info(f"Attempting to use config directory: {config_dir}")
                
                # Create directory if it doesn't exist
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                    logger.info(f"Created config directory at: {config_dir}")
                
                # Test if directory is writable by creating a test file
                test_file = os.path.join(config_dir, 'write_test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                
                if os.path.exists(test_file):
                    os.remove(test_file)
                    success = True
                    logger.info(f"Successfully verified write access to: {config_dir}")
                    break
            except Exception as e:
                error_msg = f"Failed to use config directory {config_dir}: {str(e)}"
                logger.warning(error_msg)
                error_messages.append(error_msg)
                continue
        
        if not success:
            # If all paths failed, try user's home directory as last resort
            try:
                home_dir = str(Path.home())
                config_dir = os.path.join(home_dir, 'Huntarr', 'config')
                logger.warning(f"All standard paths failed, trying home directory: {config_dir}")
                
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                
                test_file = os.path.join(config_dir, 'write_test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                
                if os.path.exists(test_file):
                    os.remove(test_file)
                    success = True
                    logger.info(f"Successfully using home directory fallback: {config_dir}")
            except Exception as e:
                error_msg = f"Failed to use home directory fallback: {str(e)}"
                logger.error(error_msg)
                error_messages.append(error_msg)
        
        # Set up file logging now that we have a logs directory
        logs_dir = os.path.join(config_dir, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        log_file = os.path.join(logs_dir, 'windows_path.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        if not success:
            logger.error("CRITICAL: Could not find a writable location for config directory!")
            logger.error("Errors encountered: " + "\n".join(error_messages))
            return None
        
        # Set up environment variables to ensure consistent path usage throughout the application
        os.environ['HUNTARR_CONFIG_DIR'] = config_dir
        os.environ['HUNTARR_LOGS_DIR'] = logs_dir
        os.environ['HUNTARR_USER_DIR'] = os.path.join(config_dir, 'user')
        os.environ['HUNTARR_STATEFUL_DIR'] = os.path.join(config_dir, 'stateful')
        
        # Create other needed directories
        for dir_name in ['user', 'stateful', 'settings']:
            dir_path = os.path.join(config_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")

        # Create a translation function to convert /config paths to Windows paths
        def convert_unix_to_windows_path(original_path):
            if platform.system() == 'Windows' and original_path and original_path.startswith('/config'):
                return original_path.replace('/config', config_dir).replace('/', '\\')
            return original_path
        
        # Monkey patch os.path.exists, os.path.isfile, open, etc. to handle /config paths
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        original_isdir = os.path.isdir
        original_open = open
        
        def patched_exists(path):
            return original_exists(convert_unix_to_windows_path(path))
        
        def patched_isfile(path):
            return original_isfile(convert_unix_to_windows_path(path))
        
        def patched_isdir(path):
            return original_isdir(convert_unix_to_windows_path(path))
        
        def patched_open(file, *args, **kwargs):
            return original_open(convert_unix_to_windows_path(file), *args, **kwargs)
        
        os.path.exists = patched_exists
        os.path.isfile = patched_isfile
        os.path.isdir = patched_isdir
        __builtins__['open'] = patched_open
        
        logger.info(f"Windows path setup complete. Using config dir: {config_dir}")
        
        # Fix for os.makedirs and similar functions
        original_makedirs = os.makedirs
        
        def patched_makedirs(path, *args, **kwargs):
            return original_makedirs(convert_unix_to_windows_path(path), *args, **kwargs)
        
        os.makedirs = patched_makedirs
        
        return config_dir
    except Exception as e:
        logger.error(f"Windows path setup failed with error: {str(e)}")
        logger.error(traceback.format_exc())
        return None

# Call setup_windows_paths automatically when imported on Windows
if platform.system() == 'Windows':
    CONFIG_DIR = setup_windows_paths()
else:
    CONFIG_DIR = "/config"  # Default for non-Windows 