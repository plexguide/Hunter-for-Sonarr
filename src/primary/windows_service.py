"""
Windows Service module for Huntarr.
Allows Huntarr to run as a Windows service.
"""

import os
import sys
import time
import logging
import traceback
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil
import pywintypes
import ctypes
from pathlib import Path

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Function to check if running as admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Configure basic logging to file in the same directory as the executable first
exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
initial_log_path = os.path.join(exe_dir, 'huntarr_service_startup.log')
logging.basicConfig(
    filename=initial_log_path,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HuntarrWindowsService')
logger.info("Starting Windows service initialization")

# Import path fix early
try:
    logger.info("Importing windows_path_fix")
    from primary.windows_path_fix import setup_windows_paths
    logger.info("Setting up Windows paths")
    config_dir = setup_windows_paths()
    logger.info(f"Config directory set to: {config_dir}")
    
    # Ensure logs dir exists for service log
    logs_dir = os.path.join(config_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.info(f"Created logs directory at: {logs_dir}")
    
    # Set up proper log file now that we have a logs directory
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'windows_service.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.info("Switched to proper log file")
except Exception as e:
    # Log the full traceback
    error_msg = f"Error during path setup: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    
    # Fall back to default path if unable to use path fix
    try:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        logs_dir = os.path.join(config_dir, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        logger.info(f"Using fallback config directory: {config_dir}")
    except Exception as fallback_error:
        # If even the fallback fails, try to write to the Windows temp directory
        logger.error(f"Fallback path also failed: {str(fallback_error)}")
        try:
            temp_dir = os.environ.get('TEMP')
            config_dir = os.path.join(temp_dir, 'Huntarr', 'config')
            logs_dir = os.path.join(config_dir, 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            logger.info(f"Using temp directory as last resort: {config_dir}")
        except Exception as temp_error:
            logger.error(f"All path options failed: {str(temp_error)}")

class HuntarrService(win32serviceutil.ServiceFramework):
    """Windows Service implementation for Huntarr"""
    
    _svc_name_ = "Huntarr"
    _svc_display_name_ = "Huntarr Service"
    _svc_description_ = "Automated media collection management for Arr apps"
    
    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = False
            socket.setdefaulttimeout(60)
            self.main_thread = None
            self.huntarr_app = None
            self.stop_flag = None
            
            # Log initialization
            servicemanager.LogInfoMsg("Huntarr service initialized")
            logger.info("Huntarr service initialized")
        except Exception as e:
            error_msg = f"Service initialization error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            servicemanager.LogErrorMsg(error_msg)
        
    def SvcStop(self):
        """Stop the service"""
        try:
            logger.info('Stopping Huntarr service...')
            servicemanager.LogInfoMsg('Stopping Huntarr service...')
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.is_running = False
            
            # Signal Huntarr to stop properly
            if hasattr(self, 'stop_flag') and self.stop_flag:
                logger.info('Setting stop flag for Huntarr...')
                self.stop_flag.set()
        except Exception as e:
            error_msg = f"Error stopping service: {e}"
            logger.error(error_msg)
            servicemanager.LogErrorMsg(error_msg)
        
    def SvcDoRun(self):
        """Run the service"""
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.is_running = True
            self.main()
        except Exception as e:
            error_msg = f"Service execution error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            servicemanager.LogErrorMsg(error_msg)
        
    def main(self):
        """Main service loop"""
        try:
            logger.info('Starting Huntarr service main loop...')
            servicemanager.LogInfoMsg('Starting Huntarr service main loop...')
            
            # Set up Windows paths again to be sure
            try:
                from primary.windows_path_fix import setup_windows_paths
                config_dir = setup_windows_paths()
                logger.info(f"Using config directory: {config_dir}")
                
                # Make sure the config_dir is set in the environment
                if config_dir:
                    os.environ['HUNTARR_CONFIG_DIR'] = config_dir
            except Exception as path_error:
                logger.error(f"Error setting up paths: {path_error}")
                servicemanager.LogErrorMsg(f"Path setup error: {path_error}")
            
            # Import here to avoid import errors when installing the service
            try:
                import threading
                from primary.background import start_huntarr, stop_event, shutdown_threads
                from primary.web_server import app
                from waitress import serve
                
                # Store the stop event for proper shutdown
                self.stop_flag = stop_event
                
                # Configure service environment
                os.environ['FLASK_HOST'] = '0.0.0.0'
                os.environ['PORT'] = '9705'
                os.environ['DEBUG'] = 'false'
                
                logger.info("Starting background thread...")
                # Start background tasks in a thread
                background_thread = threading.Thread(
                    target=start_huntarr, 
                    name="HuntarrBackground", 
                    daemon=True
                )
                background_thread.start()
                
                logger.info("Starting web server thread...")
                # Start the web server in a thread
                web_thread = threading.Thread(
                    target=lambda: serve(app, host='0.0.0.0', port=9705, threads=8),
                    name="HuntarrWebServer",
                    daemon=True
                )
                web_thread.start()
                
                logger.info('Huntarr service started successfully')
                servicemanager.LogInfoMsg('Huntarr service started successfully')
                
                # Main service loop - keep running until stop event
                restart_attempts = 0
                while self.is_running:
                    # Wait for the stop event (or timeout for checking if threads are alive)
                    event_result = win32event.WaitForSingleObject(self.stop_event, 5000)
                    
                    # Check if we should exit
                    if event_result == win32event.WAIT_OBJECT_0:
                        break
                    
                    # Check if threads are still alive
                    if not background_thread.is_alive() or not web_thread.is_alive():
                        restart_attempts += 1
                        logger.error(f"Critical: One of the Huntarr threads has died unexpectedly. Attempt {restart_attempts}/3")
                        servicemanager.LogErrorMsg(f"Thread died. Restart attempt {restart_attempts}/3")
                        
                        # Try to restart the threads if they died (limit to 3 attempts)
                        if restart_attempts <= 3:
                            if not background_thread.is_alive():
                                logger.info("Attempting to restart background thread...")
                                background_thread = threading.Thread(
                                    target=start_huntarr, 
                                    name="HuntarrBackground", 
                                    daemon=True
                                )
                                background_thread.start()
                            
                            if not web_thread.is_alive():
                                logger.info("Attempting to restart web server thread...")
                                web_thread = threading.Thread(
                                    target=lambda: serve(app, host='0.0.0.0', port=9705, threads=8),
                                    name="HuntarrWebServer",
                                    daemon=True
                                )
                                web_thread.start()
                        else:
                            logger.critical("Failed to restart threads after 3 attempts. Service will exit.")
                            servicemanager.LogErrorMsg("Failed to restart threads after 3 attempts.")
                            break
                    else:
                        # Reset restart counter if everything is working
                        restart_attempts = 0
                
                # Service is stopping, clean up
                logger.info('Huntarr service is shutting down...')
                servicemanager.LogInfoMsg('Huntarr service is shutting down...')
                
                # Set the stop event for Huntarr's background tasks
                if not stop_event.is_set():
                    stop_event.set()
                
                # Wait for threads to finish
                logger.info('Waiting for Huntarr threads to finish...')
                background_thread.join(timeout=30)
                web_thread.join(timeout=10)
                
                logger.info('Huntarr service shutdown complete')
                servicemanager.LogInfoMsg('Huntarr service shutdown complete')
                
            except Exception as import_error:
                error_msg = f"Error importing modules: {import_error}\n{traceback.format_exc()}"
                logger.error(error_msg)
                servicemanager.LogErrorMsg(error_msg)
                
        except Exception as e:
            error_msg = f"Critical error in Huntarr service: {e}\n{traceback.format_exc()}"
            logger.exception(error_msg)
            servicemanager.LogErrorMsg(f"Huntarr service error: {str(e)}")


def install_service():
    """Install Huntarr as a Windows service"""
    if sys.platform != 'win32':
        print("Windows service installation is only available on Windows.")
        return False
    
    # Check if running as admin    
    if not is_admin():
        print("ERROR: Administrator privileges are required to install the service.")
        print("Please run this command from an elevated (Run as Administrator) command prompt.")
        logger.error("Service installation failed: Not running as administrator")
        return False
        
    try:
        # Before installing, ensure the service isn't already installed
        try:
            win32serviceutil.StopService("Huntarr")
            print("Stopped existing Huntarr service before reinstallation.")
        except Exception as stop_error:
            print(f"Note: Could not stop service (it may not be running): {stop_error}")
            
        try:
            win32serviceutil.RemoveService("Huntarr")
            print("Removed existing Huntarr service before reinstallation.")
        except Exception as remove_error:
            print(f"Note: Could not remove service (it may not exist): {remove_error}")
            
        # Now install the service
        try:
            python_class_string = "src.primary.windows_service.HuntarrService"
            
            # If running from PyInstaller bundle, use a different approach
            if getattr(sys, 'frozen', False):
                # Get the path to the executable
                exe_path = sys.executable
                
                # Use os.system to run the SC command directly
                binary_path = f'"{exe_path}" --run-service'
                
                # Use os.system for administrator privileges
                cmd = f'sc create Huntarr binPath= "{binary_path}" DisplayName= "Huntarr Service" start= auto'
                logger.info(f"Creating service with command: {cmd}")
                
                ret = os.system(cmd)
                if ret != 0:
                    raise Exception(f"SC command failed with return code {ret}")
                
                # Set description
                desc_cmd = f'sc description Huntarr "Automated media collection management for Arr apps"'
                os.system(desc_cmd)
                
                print("Huntarr service installed successfully using SC command.")
            else:
                # Standard method for development environments
                win32serviceutil.InstallService(
                    pythonClassString=python_class_string,
                    serviceName="Huntarr",
                    displayName="Huntarr Service",
                    description="Automated media collection management for Arr apps",
                    startType=win32service.SERVICE_AUTO_START
                )
                print("Huntarr service installed successfully using win32serviceutil.")
            
            # Try to start the service after installation
            try:
                win32serviceutil.StartService("Huntarr")
                print("Huntarr service started successfully.")
            except Exception as start_error:
                print(f"Service installed but couldn't be started automatically: {start_error}")
                print("Try starting it manually from Windows Services.")
                
            return True
        except Exception as install_error:
            error_msg = f"Service installation failed: {str(install_error)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            print(error_msg)
            return False
            
    except Exception as e:
        print(f"Error installing Huntarr service: {e}")
        print(f"Detailed error: {traceback.format_exc()}")
        return False


def remove_service():
    """Remove the Huntarr Windows service"""
    if sys.platform != 'win32':
        print("Windows service removal is only available on Windows.")
        return False
    
    # Check if running as admin    
    if not is_admin():
        print("ERROR: Administrator privileges are required to remove the service.")
        print("Please run this command from an elevated (Run as Administrator) command prompt.")
        logger.error("Service removal failed: Not running as administrator")
        return False
        
    try:
        # Try to stop the service first
        try:
            win32serviceutil.StopService("Huntarr")
            print("Stopped Huntarr service before removal.")
            # Give it a moment to stop
            time.sleep(2)
        except Exception as stop_error:
            print(f"Note: Could not stop service (it may not be running): {stop_error}")
            
        # Now remove it
        try:
            win32serviceutil.RemoveService("Huntarr")
            print("Huntarr service removed successfully.")
            return True
        except Exception as remove_error:
            # Try using SC command as a fallback
            print(f"Could not remove service with win32serviceutil: {remove_error}")
            print("Trying to remove with SC command...")
            
            cmd = "sc delete Huntarr"
            ret = os.system(cmd)
            if ret != 0:
                raise Exception(f"SC command failed with return code {ret}")
                
            print("Huntarr service removed successfully using SC command.")
            return True
    except Exception as e:
        print(f"Error removing Huntarr service: {e}")
        print(f"Detailed error: {traceback.format_exc()}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install':
            install_service()
        elif sys.argv[1] == 'remove':
            remove_service()
        elif sys.argv[1] == '--run-service':
            # Special parameter used when the service is started by the SC command
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(HuntarrService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(HuntarrService)
    else:
        win32serviceutil.HandleCommandLine(HuntarrService)
