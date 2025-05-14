"""
Windows path fix for Huntarr
Ensures that config paths work correctly on Windows systems
"""

import os
import sys
import logging
import traceback
from pathlib import Path, WindowsPath, PurePath
import platform
import json
import builtins
import importlib

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
            if original_path is None:
                return None
            
            # Handle Path objects
            if isinstance(original_path, PurePath):
                path_str = str(original_path)
                # Check if it's an absolute path that doesn't point to the config directory
                if os.path.isabs(path_str) and not path_str.startswith('/config') and not path_str.startswith('\\config'):
                    return original_path
                
                # Convert to a string for our path conversion logic
                original_path = path_str

            # Only process string paths
            if isinstance(original_path, str):
                if platform.system() == 'Windows' and original_path.startswith('/config'):
                    return original_path.replace('/config', config_dir).replace('/', '\\')
                elif platform.system() == 'Windows' and original_path.startswith('\\config'):
                    return original_path.replace('\\config', config_dir)
            
            return original_path
        
        # --- Monkey-patch Path class to handle /config paths ---
        
        # Extend Path to add startswith method for WindowsPath
        original_windowspath = WindowsPath
        
        class PatchedWindowsPath(original_windowspath):
            def startswith(self, prefix):
                return str(self).startswith(prefix)
                
            def __truediv__(self, key):
                # Handle path division for /config paths
                result = super().__truediv__(key)
                return result
                
        # Apply the patch
        Path._flavour._WindowsFlavour.pathcls = PatchedWindowsPath
        
        # Replace the original __new__ method to intercept path creation
        original_path_new = Path.__new__
        
        def patched_path_new(cls, *args, **kwargs):
            if args and isinstance(args[0], str):
                # Convert /config paths to Windows paths
                if args[0].startswith('/config') or args[0].startswith('\\config'):
                    args = list(args)
                    args[0] = convert_unix_to_windows_path(args[0])
                    args = tuple(args)
            return original_path_new(cls, *args, **kwargs)
            
        Path.__new__ = patched_path_new
        
        # Monkey patch file operations
        original_open = builtins.open
        
        def patched_open(file, *args, **kwargs):
            converted_path = convert_unix_to_windows_path(file)
            return original_open(converted_path, *args, **kwargs)
        
        builtins.open = patched_open
        
        # Patch os.path functions
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        original_isdir = os.path.isdir
        original_join = os.path.join
        
        def patched_exists(path):
            return original_exists(convert_unix_to_windows_path(path))
        
        def patched_isfile(path):
            return original_isfile(convert_unix_to_windows_path(path))
        
        def patched_isdir(path):
            return original_isdir(convert_unix_to_windows_path(path))
        
        def patched_join(path, *paths):
            result = original_join(convert_unix_to_windows_path(path), *paths)
            return result
        
        os.path.exists = patched_exists
        os.path.isfile = patched_isfile
        os.path.isdir = patched_isdir
        os.path.join = patched_join
        
        # Fix for directory operations
        original_makedirs = os.makedirs
        original_listdir = os.listdir
        original_remove = os.remove
        
        def patched_makedirs(path, *args, **kwargs):
            return original_makedirs(convert_unix_to_windows_path(path), *args, **kwargs)
        
        def patched_listdir(path):
            return original_listdir(convert_unix_to_windows_path(path))
        
        def patched_remove(path):
            return original_remove(convert_unix_to_windows_path(path))
        
        os.makedirs = patched_makedirs
        os.listdir = patched_listdir
        os.remove = patched_remove
        
        # Patch json module for file operations
        original_json_load = json.load
        original_json_dump = json.dump
        
        def patched_json_load(fp, *args, **kwargs):
            # Just intercept for logging purposes
            try:
                return original_json_load(fp, *args, **kwargs)
            except Exception as e:
                # If the error is related to the file path, log it
                logger.error(f"Error in json.load with file: {fp}")
                raise
                
        def patched_json_dump(obj, fp, *args, **kwargs):
            # Just intercept for logging purposes
            try:
                return original_json_dump(obj, fp, *args, **kwargs)
            except Exception as e:
                # If the error is related to the file path, log it
                logger.error(f"Error in json.dump with file: {fp}")
                raise
        
        json.load = patched_json_load
        json.dump = patched_json_dump
        
        # Create empty JSON setting files if they don't exist
        logger.info("Creating empty JSON settings files...")
        for app in ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'swaparr', 'eros', 'general']:
            json_file = os.path.join(config_dir, f'{app}.json')
            if not os.path.exists(json_file):
                try:
                    with open(json_file, 'w') as f:
                        f.write('{}')
                    logger.info(f"Created empty settings file: {json_file}")
                except Exception as e:
                    logger.error(f"Error creating settings file {json_file}: {str(e)}")
        
        # Modify sys.path to ensure the proper imports can be found
        if config_dir not in sys.path:
            sys.path.append(config_dir)
        
        # Create a symlink to make /config work directly if possible
        try:
            if platform.system() == 'Windows' and not os.path.exists('/config'):
                # On Windows, symlinks require admin privileges, so this might fail
                os.symlink(config_dir, '/config')
                logger.info(f"Created symlink from {config_dir} to /config")
        except Exception as e:
            logger.debug(f"Could not create symlink (expected on Windows): {str(e)}")
        
        logger.info(f"Windows path setup complete. Using config dir: {config_dir}")
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