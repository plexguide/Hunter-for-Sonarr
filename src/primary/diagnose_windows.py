#!/usr/bin/env python3
"""
Windows diagnostics for Huntarr
This script helps diagnose common issues with Huntarr on Windows
"""

import os
import sys
import platform
import importlib
from pathlib import Path
import shutil
import traceback

print("=== Huntarr Windows Diagnostic Tool ===\n")

# Check Windows version
print(f"Windows Version: {platform.system()} {platform.version()}")
print(f"Python Version: {sys.version}")
print(f"Current Directory: {os.getcwd()}")
print(f"Script Path: {os.path.abspath(__file__)}")

# Try to load the Windows path fix module
print("\n=== Testing Windows Path Fix ===")
try:
    from src.primary.windows_path_fix import setup_windows_paths
    config_dir = setup_windows_paths()
    print(f"Config directory: {config_dir}")
    if config_dir:
        print("Windows path fix module loaded successfully")
    else:
        print("WARNING: Windows path fix module loaded but config_dir is None")
except Exception as e:
    print(f"ERROR: Failed to load windows_path_fix: {str(e)}")
    print(traceback.format_exc())

# Check Flask is installed
print("\n=== Testing Flask Installation ===")
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("ERROR: Flask is not installed or not importable")

# Check if running as frozen application
print("\n=== Execution Environment ===")
is_frozen = getattr(sys, 'frozen', False)
print(f"Running as PyInstaller bundle: {is_frozen}")
if is_frozen:
    print(f"Executable path: {sys.executable}")
    bundle_dir = os.path.dirname(sys.executable)
    print(f"Bundle directory: {bundle_dir}")
else:
    print("Running as script")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(f"Project root: {root_dir}")

# Test template directories
print("\n=== Template Directory Test ===")
template_dirs = []

# Check environment variables first
env_template_dir = os.environ.get('TEMPLATE_FOLDER')
if env_template_dir:
    template_dirs.append(("Environment Variable", env_template_dir))

# Check PyInstaller bundle location if frozen
if is_frozen:
    bundle_template_dir = os.path.join(os.path.dirname(sys.executable), 'templates')
    template_dirs.append(("PyInstaller Bundle", bundle_template_dir))

# Check default frontend location
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
frontend_template_dir = os.path.join(root_dir, 'frontend', 'templates')
template_dirs.append(("Frontend", frontend_template_dir))

# Check current directory
current_dir_template = os.path.join(os.getcwd(), 'templates')
template_dirs.append(("Current Directory", current_dir_template))

for source, template_dir in template_dirs:
    print(f"\nChecking {source} template directory: {template_dir}")
    if os.path.exists(template_dir):
        print(f"  - Directory exists")
        try:
            contents = os.listdir(template_dir)
            print(f"  - Contents: {contents}")
            
            # Check for required templates
            has_setup = os.path.exists(os.path.join(template_dir, 'setup.html'))
            has_index = os.path.exists(os.path.join(template_dir, 'index.html'))
            
            print(f"  - setup.html exists: {has_setup}")
            print(f"  - index.html exists: {has_index}")
            
            if has_setup and has_index:
                print("  - GOOD: All required templates exist")
            else:
                print("  - WARNING: Missing required templates")
        except Exception as e:
            print(f"  - ERROR: {str(e)}")
    else:
        print(f"  - Directory does not exist")

# Test template string extraction
print("\n=== Template Content Test ===")
try:
    from src.primary.setup_html import SETUP_HTML, INDEX_HTML, extract_templates
    
    print("setup_html.py module loaded successfully")
    
    if "<!DOCTYPE html>" in SETUP_HTML and "<html" in SETUP_HTML:
        print("SETUP_HTML content looks valid")
    else:
        print("WARNING: SETUP_HTML content may be incomplete")
        
    if "<!DOCTYPE html>" in INDEX_HTML and "<html" in INDEX_HTML:
        print("INDEX_HTML content looks valid")
    else:
        print("WARNING: INDEX_HTML content may be incomplete")
    
    # Try extracting templates to a test directory
    test_dir = os.path.join(os.getcwd(), 'templates_test')
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    print(f"Testing extract_templates to: {test_dir}")
    extract_templates(test_dir)
    
    if os.path.exists(os.path.join(test_dir, 'setup.html')) and os.path.exists(os.path.join(test_dir, 'index.html')):
        print("Template extraction successful")
    else:
        print("WARNING: Template extraction may have failed")
except Exception as e:
    print(f"Error testing setup_html.py: {str(e)}")
    print(traceback.format_exc())

# Test Flask configuration
print("\n=== Flask Configuration Test ===")
try:
    import flask
    from flask import Flask, render_template_string
    
    # Create a minimal test Flask app
    test_app = Flask(__name__)
    
    # Get actual template folder from environment or use default
    template_folder = os.environ.get('TEMPLATE_FOLDER')
    if template_folder and os.path.exists(template_folder):
        test_app.template_folder = template_folder
        print(f"Using template folder from environment: {template_folder}")
    else:
        print(f"Using Flask default template folder: {test_app.template_folder}")
    
    print(f"Flask import path: {flask.__file__}")
    print(f"Flask template folder: {test_app.template_folder}")
    print(f"Flask static folder: {test_app.static_folder}")
    
    # Test direct template string rendering
    try:
        result = render_template_string("<html><body>Test template</body></html>")
        print("Template string rendering: SUCCESS")
    except Exception as e:
        print(f"Template string rendering error: {str(e)}")
except Exception as e:
    print(f"Flask configuration test error: {str(e)}")

print("\n=== Diagnostic Complete ===") 