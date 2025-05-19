"""
Windows Service module for Huntarr.
Allows Huntarr to run as a Windows service.
Includes privilege checks and fallback mechanisms for non-admin users.
"""

import os
import sys
import time
import logging
import servicemanager
import socket
import ctypes
import win32event
import win32service
import win32security
import win32serviceutil
import win32api
import win32con

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import our config paths module early to ensure proper path setup
try:
    from primary.utils import config_paths
    config_dir = config_paths.CONFIG_DIR
    logs_dir = config_paths.LOGS_DIR
except Exception as e:
    # Fallback if config_paths module can't be imported yet
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    logs_dir = os.path.join(config_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

# Configure basic logging
logging.basicConfig(
    filename=os.path.join(logs_dir, 'windows_service.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HuntarrWindowsService')

class HuntarrService(win32serviceutil.ServiceFramework):
    """Windows Service implementation for Huntarr"""
    
    _svc_name_ = "Huntarr"
    _svc_display_name_ = "Huntarr Service"
    _svc_description_ = "Automated media collection management for Arr apps"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = False
        socket.setdefaulttimeout(60)
        self.main_thread = None
        self.huntarr_app = None
        self.stop_flag = None
        
    def SvcStop(self):
        """Stop the service"""
        logger.info('Stopping Huntarr service...')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False
        
        # Signal Huntarr to stop properly
        if hasattr(self, 'stop_flag') and self.stop_flag:
            logger.info('Setting stop flag for Huntarr...')
            self.stop_flag.set()
        
    def SvcDoRun(self):
        """Run the service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.is_running = True
        self.main()
        
    def main(self):
        """Main service loop"""
        try:
            logger.info('Starting Huntarr service...')
            
            # Import here to avoid import errors when installing the service
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
            
            # Start background tasks in a thread
            background_thread = threading.Thread(
                target=start_huntarr, 
                name="HuntarrBackground", 
                daemon=True
            )
            background_thread.start()
            
            # Start the web server in a thread
            web_thread = threading.Thread(
                target=lambda: serve(app, host='0.0.0.0', port=9705, threads=8),
                name="HuntarrWebServer",
                daemon=True
            )
            web_thread.start()
            
            logger.info('Huntarr service started successfully')
            
            # Main service loop - keep running until stop event
            while self.is_running:
                # Wait for the stop event (or timeout for checking if threads are alive)
                event_result = win32event.WaitForSingleObject(self.stop_event, 5000)
                
                # Check if we should exit
                if event_result == win32event.WAIT_OBJECT_0:
                    break
                
                # Check if threads are still alive
                if not background_thread.is_alive() or not web_thread.is_alive():
                    logger.error("Critical: One of the Huntarr threads has died unexpectedly")
                    # Try to restart the threads if they died
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
            
            # Service is stopping, clean up
            logger.info('Huntarr service is shutting down...')
            
            # Set the stop event for Huntarr's background tasks
            if not stop_event.is_set():
                stop_event.set()
            
            # Wait for threads to finish
            logger.info('Waiting for Huntarr threads to finish...')
            background_thread.join(timeout=30)
            web_thread.join(timeout=10)
            
            logger.info('Huntarr service shutdown complete')
            
        except Exception as e:
            logger.exception(f"Critical error in Huntarr service: {e}")
            servicemanager.LogErrorMsg(f"Huntarr service error: {str(e)}")


def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def install_service():
    """Install Huntarr as a Windows service"""
    if sys.platform != 'win32':
        print("Windows service installation is only available on Windows.")
        return False
    
    # Check for administrator privileges
    if not is_admin():
        print("ERROR: Administrator privileges required to install the service.")
        print("Please right-click on the installer or command prompt and select 'Run as administrator'.")
        print("Alternatively, you can run Huntarr directly without service installation using 'python main.py'.")
        return False
        
    try:
        # Get the Python executable path for service registration
        python_exe = sys.executable
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'main.py'))
        
        # Ensure service has necessary permissions
        service_acl = win32security.SECURITY_ATTRIBUTES()
        service_dacl = win32security.ACL()
        service_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
            win32security.TokenUser
        )[0]
        service_dacl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.GENERIC_ALL, service_sid)
        service_acl.SetSecurityDescriptorDacl(1, service_dacl, 0)
        
        # Install the service with proper permissions
        win32serviceutil.InstallService(
            pythonClassString="src.primary.windows_service.HuntarrService",
            serviceName="Huntarr",
            displayName="Huntarr Service",
            description="Automated media collection management for Arr apps",
            startType=win32service.SERVICE_AUTO_START,
            exeName=python_exe,
            exeArgs=f'"{script_path}" --service'
        )
        
        # Set more permissive service permissions
        try:
            hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            hs = win32service.OpenService(hscm, "Huntarr", win32service.SERVICE_ALL_ACCESS)
            
            # Configure service to allow interaction with desktop
            service_config = win32service.QueryServiceConfig(hs)
            win32service.ChangeServiceConfig(
                hs,
                service_config[0],  # Service type
                service_config[1],  # Start type
                service_config[2] | win32service.SERVICE_INTERACTIVE_PROCESS,  # Error control & flags
                service_config[3],  # Binary path
                service_config[4],  # Load order group
                service_config[5],  # Tag ID
                service_config[6],  # Dependencies
                service_config[7],  # Service start name
                service_config[8],  # Password
                service_config[9]   # Display name
            )
            win32service.CloseServiceHandle(hs)
            win32service.CloseServiceHandle(hscm)
        except Exception as e:
            logger.warning(f"Could not set interactive permissions: {e}")
            # Continue anyway, as this is not critical
        
        # Start the service
        try:
            win32serviceutil.StartService("Huntarr")
            print("Huntarr service installed and started successfully.")
        except Exception as e:
            print(f"Service installed but failed to start automatically: {e}")
            print("You can try starting it manually from Services control panel,")
            print("or run Huntarr directly using 'python main.py'.")
        
        return True
    except Exception as e:
        print(f"Error installing Huntarr service: {e}")
        print("Fallback: You can run Huntarr directly without service installation using 'python main.py'.")
        return False


def remove_service():
    """Remove the Huntarr Windows service"""
    if sys.platform != 'win32':
        print("Windows service removal is only available on Windows.")
        return False
    
    # Check for administrator privileges
    if not is_admin():
        print("ERROR: Administrator privileges required to remove the service.")
        print("Please right-click on the command prompt and select 'Run as administrator'.")
        return False
        
    try:
        # Stop the service first if it's running
        try:
            win32serviceutil.StopService("Huntarr")
            print("Huntarr service stopped.")
            time.sleep(2)  # Wait for service to fully stop
        except Exception as e:
            print(f"Note: Could not stop the service (it may already be stopped): {e}")
        
        # Now remove the service
        win32serviceutil.RemoveService("Huntarr")
        print("Huntarr service removed successfully.")
        return True
    except Exception as e:
        print(f"Error removing Huntarr service: {e}")
        return False


def run_as_cli():
    """Run Huntarr as a command-line application (non-service fallback)"""
    try:
        # Import required modules
        import threading
        from primary.background import start_huntarr, stop_event
        from primary.web_server import app
        from waitress import serve
        
        print("Starting Huntarr in command-line mode...")
        
        # Start background tasks in a thread
        background_thread = threading.Thread(
            target=start_huntarr, 
            name="HuntarrBackground", 
            daemon=True
        )
        background_thread.start()
        
        # Run the web server directly (blocking)
        print("Starting web server on http://localhost:9705")
        print("Press Ctrl+C to stop")
        serve(app, host='0.0.0.0', port=9705, threads=8)
    except KeyboardInterrupt:
        print("\nStopping Huntarr...")
        if not stop_event.is_set():
            stop_event.set()
        # Give threads time to clean up
        time.sleep(2)
    except Exception as e:
        print(f"Error running Huntarr in command-line mode: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install':
            install_service()
        elif sys.argv[1] == 'remove':
            remove_service()
        elif sys.argv[1] == 'cli':
            run_as_cli()
        else:
            win32serviceutil.HandleCommandLine(HuntarrService)
    else:
        win32serviceutil.HandleCommandLine(HuntarrService)
