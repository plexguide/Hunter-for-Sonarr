"""
Windows Service module for Huntarr.
Allows Huntarr to run as a Windows service.
"""

import os
import sys
import time
import logging
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure basic logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                         'config', 'logs', 'windows_service.log'),
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


def install_service():
    """Install Huntarr as a Windows service"""
    if sys.platform != 'win32':
        print("Windows service installation is only available on Windows.")
        return False
        
    try:
        win32serviceutil.InstallService(
            pythonClassString="src.primary.windows_service.HuntarrService",
            serviceName="Huntarr",
            displayName="Huntarr Service",
            description="Automated media collection management for Arr apps",
            startType=win32service.SERVICE_AUTO_START
        )
        print("Huntarr service installed successfully.")
        return True
    except Exception as e:
        print(f"Error installing Huntarr service: {e}")
        return False


def remove_service():
    """Remove the Huntarr Windows service"""
    if sys.platform != 'win32':
        print("Windows service removal is only available on Windows.")
        return False
        
    try:
        win32serviceutil.RemoveService("Huntarr")
        print("Huntarr service removed successfully.")
        return True
    except Exception as e:
        print(f"Error removing Huntarr service: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install':
            install_service()
        elif sys.argv[1] == 'remove':
            remove_service()
        else:
            win32serviceutil.HandleCommandLine(HuntarrService)
    else:
        win32serviceutil.HandleCommandLine(HuntarrService)
