"""
Windows path fix for Huntarr
Ensures that config paths work correctly on Windows systems
"""

import os
import sys
import logging
import traceback
from pathlib import Path

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
        
        if not success:
            logger.error("CRITICAL: Could not find a writable location for config directory!")
            logger.error("Errors encountered: " + "\n".join(error_messages))
            return None
        
        # Ensure logs directory exists
        logs_dir = os.path.join(config_dir, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            logger.info(f"Created logs directory at: {logs_dir}")
        
        # Set environment variable for other parts of the app to use
        os.environ['HUNTARR_CONFIG_DIR'] = config_dir
        
        # Set up file logging now that we have a logs directory
        file_handler = logging.FileHandler(os.path.join(logs_dir, 'windows_path.log'))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info(f"Windows path setup complete. Using config dir: {config_dir}")
        return config_dir
    except Exception as e:
        full_traceback = traceback.format_exc()
        logger.error(f"Error setting up Windows paths: {e}")
        logger.error(f"Traceback: {full_traceback}")
        
        # Try to write error to a file somewhere accessible
        try:
            error_file = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(), 'huntarr_error.log')
            with open(error_file, 'a') as f:
                f.write(f"Error setting up Windows paths: {e}\n")
                f.write(f"Traceback: {full_traceback}\n")
        except:
            pass  # If this fails too, we've done all we can
            
        return None 