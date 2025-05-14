"""
Windows path fix for Huntarr
Ensures that config paths work correctly on Windows systems
"""

import os
import sys
import logging
import traceback
from pathlib import Path, PurePath
import platform
import json
import builtins
import importlib
import shutil

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
        needed_dirs = ['user', 'stateful', 'settings', 'scheduler', 'tally']
        for dir_name in needed_dirs:
            dir_path = os.path.join(config_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")

        # Ensure templates directory exists and has necessary files
        templates_dir = os.path.join(app_path, "templates")
        static_dir = os.path.join(app_path, "static")
        
        try:
            # Create templates and static directories if they don't exist
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
                logger.info(f"Created templates directory at: {templates_dir}")
                
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)
                logger.info(f"Created static directory at: {static_dir}")
                
            # Copy frontend files from src/frontend if they exist
            frontend_dir = os.path.join(app_path, "src", "frontend")
            if os.path.exists(frontend_dir):
                logger.info(f"Copying frontend files from {frontend_dir}")
                try:
                    # Copy all files from frontend/templates to templates
                    frontend_templates = os.path.join(frontend_dir, "templates")
                    if os.path.exists(frontend_templates):
                        for file in os.listdir(frontend_templates):
                            src_file = os.path.join(frontend_templates, file)
                            dest_file = os.path.join(templates_dir, file)
                            if os.path.isfile(src_file):
                                shutil.copy2(src_file, dest_file)
                                logger.info(f"Copied template file: {file}")
                    
                    # Copy all files from frontend/static to static
                    frontend_static = os.path.join(frontend_dir, "static")
                    if os.path.exists(frontend_static):
                        for root, dirs, files in os.walk(frontend_static):
                            for file in files:
                                src_file = os.path.join(root, file)
                                rel_path = os.path.relpath(src_file, frontend_static)
                                dest_file = os.path.join(static_dir, rel_path)
                                dest_dir = os.path.dirname(dest_file)
                                if not os.path.exists(dest_dir):
                                    os.makedirs(dest_dir)
                                shutil.copy2(src_file, dest_file)
                                logger.info(f"Copied static file: {rel_path}")
                except Exception as e:
                    logger.error(f"Error copying frontend files: {str(e)}")
        except Exception as e:
            logger.error(f"Error setting up template directories: {str(e)}")

        # Create a translation function to convert /config paths to Windows paths
        def convert_unix_to_windows_path(original_path):
            if original_path is None:
                return None
                
            # Convert to string if it's a Path object
            if isinstance(original_path, PurePath):
                original_path = str(original_path)
                
            # Only process string paths
            if isinstance(original_path, str):
                if original_path.startswith('/config'):
                    return original_path.replace('/config', config_dir).replace('/', '\\')
                elif original_path.startswith('\\config'):
                    return original_path.replace('\\config', config_dir)
                
            return original_path
        
        # Add a startswith method to the PathLib Path class if needed
        if platform.system() == 'Windows' and not hasattr(Path, 'startswith'):
            # Create a safer monkey patch that doesn't mess with internal attributes
            original_path_str = Path.__str__
            
            def patch_startswith(self, prefix):
                return str(self).startswith(prefix)
                
            # Add the startswith method to Path
            Path.startswith = patch_startswith
            
            logger.info("Added startswith method to Path class")
            
        # Create json config files
        for app in ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'swaparr', 'eros', 'general']:
            json_file = os.path.join(config_dir, f'{app}.json')
            if not os.path.exists(json_file):
                try:
                    with open(json_file, 'w') as f:
                        f.write('{}')
                    logger.info(f"Created empty settings file: {json_file}")
                except Exception as e:
                    logger.error(f"Error creating settings file {json_file}: {str(e)}")
                    
        # Create empty scheduler file
        scheduler_file = os.path.join(config_dir, 'scheduler', 'schedule.json')
        if not os.path.exists(scheduler_file):
            try:
                scheduler_dir = os.path.dirname(scheduler_file)
                if not os.path.exists(scheduler_dir):
                    os.makedirs(scheduler_dir)
                with open(scheduler_file, 'w') as f:
                    f.write('{"schedules":[]}')
                logger.info(f"Created empty scheduler file: {scheduler_file}")
            except Exception as e:
                logger.error(f"Error creating scheduler file {scheduler_file}: {str(e)}")
                
        # Create tally tracking files
        tally_dir = os.path.join(config_dir, 'tally')
        if not os.path.exists(tally_dir):
            os.makedirs(tally_dir)
            
        media_stats_file = os.path.join(tally_dir, 'media_stats.json')
        if not os.path.exists(media_stats_file):
            try:
                with open(media_stats_file, 'w') as f:
                    f.write('{}')
                logger.info(f"Created empty media stats file: {media_stats_file}")
            except Exception as e:
                logger.error(f"Error creating media stats file {media_stats_file}: {str(e)}")
                
        hourly_cap_file = os.path.join(tally_dir, 'hourly_cap.json')
        if not os.path.exists(hourly_cap_file):
            try:
                with open(hourly_cap_file, 'w') as f:
                    f.write('{}')
                logger.info(f"Created empty hourly cap file: {hourly_cap_file}")
            except Exception as e:
                logger.error(f"Error creating hourly cap file {hourly_cap_file}: {str(e)}")
        
        # Monkey patch the open function and os.path operations
        original_open = builtins.open
        
        def patched_open(file, *args, **kwargs):
            # Skip binary files (prevent errors with non-string file paths)
            if len(args) > 0 and 'b' in args[0]:
                return original_open(file, *args, **kwargs)
                
            try:
                # Convert the path if it's a string or Path object
                if isinstance(file, (str, PurePath)):
                    converted_path = convert_unix_to_windows_path(file)
                    return original_open(converted_path, *args, **kwargs)
                return original_open(file, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in patched_open with path {file}: {str(e)}")
                raise
        
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
            # Only process the first argument (the base path)
            converted_path = convert_unix_to_windows_path(path)
            if converted_path != path:
                return original_join(converted_path, *paths)
            return original_join(path, *paths)
        
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
        
        # Modify sys.path to ensure all imports work
        if config_dir not in sys.path:
            sys.path.append(config_dir)
            
        if app_path not in sys.path:
            sys.path.append(app_path)
            
        # Set Flask environment variables 
        os.environ['FLASK_APP'] = 'src.primary.web_server'
        os.environ['TEMPLATE_FOLDER'] = templates_dir
        os.environ['STATIC_FOLDER'] = static_dir
        
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