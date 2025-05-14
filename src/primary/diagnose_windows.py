"""
Windows diagnostic tool for Huntarr.
Helps identify common issues with Huntarr installations on Windows.
"""

import os
import sys
import importlib
import traceback
import socket

def check_dependency(module_name, package_name=None):
    """Check if a Python dependency is installed and can be imported."""
    if package_name is None:
        package_name = module_name
        
    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name} is installed and importable")
        return True
    except ImportError as e:
        print(f"✗ {package_name} is NOT installed or not importable: {str(e)}")
        return False

def check_port(port=9705):
    """Check if the specified port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Try to bind to the port
            s.bind(('127.0.0.1', port))
            print(f"✓ Port {port} is available")
            return True
    except socket.error:
        print(f"✗ Port {port} is already in use by another application")
        return False

def check_admin():
    """Check if running with administrator privileges."""
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("✓ Running with administrator privileges")
        else:
            print("✗ Not running with administrator privileges")
        return is_admin
    except Exception as e:
        print(f"✗ Could not check administrator privileges: {str(e)}")
        return False

def check_service_status():
    """Check if the Huntarr service is installed and its status."""
    try:
        import win32serviceutil
        import win32service
        
        try:
            status = win32serviceutil.QueryServiceStatus("Huntarr")
            status_map = {
                win32service.SERVICE_STOPPED: "STOPPED",
                win32service.SERVICE_START_PENDING: "START PENDING",
                win32service.SERVICE_STOP_PENDING: "STOP PENDING",
                win32service.SERVICE_RUNNING: "RUNNING",
                win32service.SERVICE_CONTINUE_PENDING: "CONTINUE PENDING",
                win32service.SERVICE_PAUSE_PENDING: "PAUSE PENDING",
                win32service.SERVICE_PAUSED: "PAUSED"
            }
            status_str = status_map.get(status[1], f"UNKNOWN ({status[1]})")
            print(f"✓ Huntarr service is installed, current status: {status_str}")
            return True
        except Exception:
            print("✗ Huntarr service is not installed or accessible")
            return False
    except ImportError:
        print("✗ Could not check service status: win32serviceutil not available")
        return False

def check_config_directory():
    """Check if the config directory exists and is writable."""
    try:
        # First try to use the windows_path_fix module
        try:
            from primary.windows_path_fix import setup_windows_paths
            config_dir = setup_windows_paths()
            if config_dir:
                print(f"✓ Config directory created and writable: {config_dir}")
                return True
            else:
                print("✗ Failed to set up config directory using windows_path_fix")
                return False
        except ImportError:
            print("✗ Could not import windows_path_fix module")
            
            # Try to check some common locations
            potential_dirs = []
            
            # If running as PyInstaller bundle
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                potential_dirs.append(os.path.join(exe_dir, 'config'))
                
            # ProgramData location
            potential_dirs.append(os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Huntarr', 'config'))
            
            # Local AppData location
            potential_dirs.append(os.path.join(os.environ.get('LOCALAPPDATA', 'C:\\Users\\' + os.environ.get('USERNAME', 'Default') + '\\AppData\\Local'), 'Huntarr', 'config'))
            
            # Home directory
            from pathlib import Path
            home_dir = str(Path.home())
            potential_dirs.append(os.path.join(home_dir, 'Huntarr', 'config'))
            
            for dir_path in potential_dirs:
                if os.path.exists(dir_path):
                    # Check if it's writable
                    try:
                        test_file = os.path.join(dir_path, 'write_test.tmp')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        if os.path.exists(test_file):
                            os.remove(test_file)
                            print(f"✓ Found existing writable config directory: {dir_path}")
                            return True
                    except:
                        pass
                    
            print("✗ Could not find a writable config directory")
            return False
            
    except Exception as e:
        print(f"✗ Error checking config directory: {str(e)}")
        return False

def run_diagnostics():
    """Run all diagnostic checks."""
    print("=" * 50)
    print("HUNTARR WINDOWS DIAGNOSTICS")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Executable: {sys.executable}")
    print(f"Frozen: {getattr(sys, 'frozen', False)}")
    print("=" * 50)
    
    # Check administrator privileges
    admin = check_admin()
    
    # Basic dependency checks
    print("\nChecking core dependencies:")
    check_dependency('flask', 'Flask')
    check_dependency('waitress')
    check_dependency('requests')
    check_dependency('bcrypt')
    check_dependency('qrcode')
    check_dependency('pyotp')
    
    # Flask-specific dependencies
    print("\nChecking Flask dependencies:")
    check_dependency('werkzeug')
    check_dependency('jinja2')
    check_dependency('markupsafe')
    check_dependency('itsdangerous')
    
    # Windows-specific dependencies
    print("\nChecking Windows-specific dependencies:")
    check_dependency('win32serviceutil', 'pywin32')
    check_dependency('win32service', 'pywin32')
    check_dependency('win32event', 'pywin32')
    check_dependency('servicemanager', 'pywin32')
    
    # Environment checks
    print("\nChecking environment:")
    check_port()
    check_config_directory()
    
    # Service checks
    print("\nChecking Huntarr service:")
    check_service_status()
    
    print("\nDiagnostic Summary:")
    print("If you see any '✗' marks above, those indicate issues that need to be addressed.")
    print("For detailed troubleshooting assistance, please visit:")
    print("https://github.com/plexguide/Huntarr.io")

if __name__ == "__main__":
    try:
        run_diagnostics()
    except Exception as e:
        print("=" * 50)
        print("DIAGNOSTIC TOOL CRASHED")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc() 