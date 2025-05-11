"""
Windows Launcher Module for Huntarr
Provides a visible interface when running the application on Windows
"""
import os
import sys
import threading
import webbrowser
import time
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import signal
import atexit

# When running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASEDIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASEDIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import Huntarr components after setting paths
sys.path.insert(0, BASEDIR)
sys.path.insert(0, os.path.join(BASEDIR, 'src'))

try:
    # We'll import these from main application
    from primary.utils.logger import setup_main_logger, get_logger
    from primary.web_server import app
    from primary.background import start_huntarr, stop_event, shutdown_threads
except ImportError as e:
    # If imports fail, show dialog to user and exit
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Huntarr Import Error", 
                         f"Failed to import Huntarr components: {e}\n\n"
                         "Please ensure all dependencies are installed and the application structure is correct.")
    root.destroy()
    sys.exit(1)

class HuntarrLauncher:
    """Windows GUI launcher for Huntarr"""
    
    def __init__(self):
        self.logger = get_logger("HuntarrLauncher")
        self.is_running = False
        self.host = '127.0.0.1'
        self.port = 5000  # Default port
        self.url = f"http://{self.host}:{self.port}"
        self.stop_event = stop_event
        
        # Set up the GUI window
        self.root = tk.Tk()
        self.root.title("Huntarr")
        self.root.geometry("400x320")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set icon if available
        icon_path = os.path.join(BASEDIR, 'frontend', 'static', 'img', 'logo', 'huntarr.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                self.logger.warning(f"Failed to load icon from {icon_path}")
        
        self.setup_ui()
        
        # Register cleanup
        atexit.register(self.cleanup)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo
        logo_path = os.path.join(BASEDIR, 'frontend', 'static', 'img', 'logo', 'huntarr.png')
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((120, 120), Image.LANCZOS)
                logo_tk = ImageTk.PhotoImage(logo_img)
                logo_label = ttk.Label(main_frame, image=logo_tk)
                logo_label.image = logo_tk  # Keep a reference
                logo_label.pack(pady=10)
            except ImportError:
                # Fallback if PIL is not available
                title_label = ttk.Label(main_frame, text="HUNTARR", font=("Arial", 24, "bold"))
                title_label.pack(pady=10)
                self.logger.warning("PIL not available, using text title instead of logo")
        else:
            title_label = ttk.Label(main_frame, text="HUNTARR", font=("Arial", 24, "bold"))
            title_label.pack(pady=10)
            
        # Status 
        self.status_text = tk.StringVar(value="Click Start to launch Huntarr")
        status_label = ttk.Label(main_frame, textvariable=self.status_text, font=("Arial", 10))
        status_label.pack(pady=5)
        
        # Server address
        self.url_text = tk.StringVar(value=self.url)
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="Server URL:").pack(side=tk.LEFT, padx=5)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_text, state="readonly", width=30)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10, fill=tk.X)
        
        # Start button
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Open browser button
        self.browser_btn = ttk.Button(btn_frame, text="Open in Browser", command=self.open_browser, state=tk.DISABLED)
        self.browser_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Stop button
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
    def start_server(self):
        """Start the Huntarr server and background tasks"""
        if self.is_running:
            return
            
        # Update UI
        self.status_text.set("Starting Huntarr server...")
        self.start_btn.config(state=tk.DISABLED)
        self.progress.start()
        
        # Run server in a separate thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        # Check if server started
        self.root.after(2000, self.check_server_status)
        
    def run_server(self):
        """Run the actual server process"""
        try:
            # Start the background tasks
            background_thread = threading.Thread(target=start_huntarr, daemon=True)
            background_thread.start()
            
            # Import and run web server
            from primary.web_server import run_server
            run_server(host=self.host, port=self.port)
        except Exception as e:
            self.logger.exception(f"Error starting server: {e}")
            self.status_text.set(f"Error: {str(e)}")
            self.progress.stop()
            self.start_btn.config(state=tk.NORMAL)
    
    def check_server_status(self):
        """Check if the server is running and update UI"""
        import requests
        try:
            response = requests.get(f"{self.url}/api/status", timeout=0.5)
            if response.status_code == 200:
                self.is_running = True
                self.status_text.set("Huntarr is running")
                self.browser_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.NORMAL)
                self.progress.stop()
                self.open_browser()  # Auto-open browser
                return
        except requests.RequestException:
            # Server might still be starting
            pass
            
        # Try again in 1 second if not started
        if not self.stop_event.is_set():
            self.root.after(1000, self.check_server_status)
        else:
            self.status_text.set("Server failed to start")
            self.progress.stop()
            self.start_btn.config(state=tk.NORMAL)
    
    def stop_server(self):
        """Stop the server"""
        if not self.is_running:
            return
            
        self.status_text.set("Stopping Huntarr...")
        self.progress.start()
        self.stop_btn.config(state=tk.DISABLED)
        self.browser_btn.config(state=tk.DISABLED)
        
        # Set stop event to signal shutdown
        if not self.stop_event.is_set():
            self.stop_event.set()
            
        # Schedule check for server shutdown
        self.root.after(1000, self.check_stopped)
        
    def check_stopped(self):
        """Check if server has stopped"""
        import requests
        try:
            response = requests.get(f"{self.url}/api/status", timeout=0.5)
            # If we can still connect, server is running
            self.root.after(1000, self.check_stopped)
        except requests.RequestException:
            # If connection fails, server likely stopped
            self.is_running = False
            self.status_text.set("Huntarr stopped")
            self.progress.stop()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.browser_btn.config(state=tk.DISABLED)
            
    def open_browser(self):
        """Open the default browser to the Huntarr web interface"""
        webbrowser.open(self.url)
        
    def on_close(self):
        """Handle window close event"""
        if self.is_running:
            if messagebox.askyesno("Confirm Exit", 
                                  "Huntarr is still running.\nDo you want to stop the server and exit?"):
                self.stop_server()
                self.root.after(1500, self.root.destroy)
            # Don't close if user cancels
        else:
            self.root.destroy()
            
    def signal_handler(self, signum, frame):
        """Handle OS signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop_server()
        self.root.after(1500, self.root.destroy)
        
    def cleanup(self):
        """Clean up resources"""
        if self.is_running and not self.stop_event.is_set():
            self.stop_event.set()
            
    def run(self):
        """Run the launcher main loop"""
        self.root.mainloop()
        
def main():
    """Main entry point for the launcher"""
    # Configure the logger
    setup_main_logger()
    logger = get_logger("WindowsLauncher")
    logger.info("Starting Huntarr Windows Launcher")
    
    # Start the launcher
    launcher = HuntarrLauncher()
    launcher.run()
    
if __name__ == "__main__":
    main()
