#!/usr/bin/env python3
"""
Generate a PyInstaller spec file for Huntarr
"""

import os
import sys

def generate_spec_file(output_path='huntarr.spec'):
    """
    Generate a PyInstaller spec file for Huntarr
    """
    # Get the current working directory
    cwd = os.getcwd()
    
    # Debug - print information about the environment
    print(f"Current working directory: {cwd}")
    print(f"Directory contents: {os.listdir(cwd)}")
    
    # Check if required directories exist
    required_dirs = ['src', 'templates', 'static', 'assets']
    for directory in required_dirs:
        if os.path.exists(os.path.join(cwd, directory)):
            print(f" Found directory: {directory}")
        else:
            print(f" Missing directory: {directory}")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Debug information - will be shown in build logs
print("===== PYINSTALLER SPEC EXECUTION =====")
print(f"Current working directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Function to safely resolve paths
def safe_path(path):
    if os.path.exists(path):
        print(f"Path exists: {path}")
        return path
    else:
        print(f"Path does not exist: {path}")
        # Try parent directory as fallback
        parent_path = os.path.abspath(os.path.join(os.getcwd(), '..', os.path.basename(path)))
        if os.path.exists(parent_path):
            print(f"Using alternative path: {parent_path}")
            return parent_path
        print(f"Alternative path not found either: {parent_path}")
        # Use the original path and let PyInstaller warn about it
        return path

# List of data directories to include
data_dirs = []
for dir_name in ['src', 'templates', 'static', 'assets']:
    full_path = os.path.join(os.getcwd(), dir_name)
    if os.path.exists(full_path):
        data_dirs.append((full_path, dir_name))
        print(f"Adding directory: {full_path} -> {dir_name}")
    else:
        print(f"Warning: Could not find directory: {full_path}")

# List of data files to include
data_files = []
for file_name in ['requirements.txt', 'version.txt']:
    full_path = os.path.join(os.getcwd(), file_name)
    if os.path.exists(full_path):
        data_files.append((full_path, '.'))
        print(f"Adding file: {full_path}")
    else:
        print(f"Warning: Could not find file: {full_path}")

# Get icon path
icon_path = None  # Default to None to avoid icon issues in GitHub Actions
if not os.environ.get('CI'):  # Only use icon in local builds, not in CI
    potential_icon_path = os.path.join(os.getcwd(), 'assets', 'huntarr.ico')
    if os.path.exists(potential_icon_path):
        print(f"Found icon file: {potential_icon_path}")
        icon_path = potential_icon_path
    else:
        print(f"Warning: Icon file not found: {potential_icon_path}")
        # Try to find the icon elsewhere
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file == 'huntarr.ico':
                    icon_path = os.path.join(root, file)
                    print(f"Found icon at alternative location: {icon_path}")
                    break
            if icon_path:
                break
else:
    print("Running in CI environment, skipping icon to avoid format issues")

# Combine all datas
all_datas = data_dirs + data_files

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=all_datas,
    hiddenimports=[
        'flask', 'waitress', 'requests', 'dateutil', 'pyotp', 'qrcode', 'psutil', 'pytz',
        'win32timezone', 'win32serviceutil', 'win32service', 'win32event', 'servicemanager', 'socket',
        'src.primary.windows_service'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Huntarr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Changed to True to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)
"""
    
    # Write spec file
    with open(output_path, 'w') as f:
        f.write(spec_content)
    
    print(f"PyInstaller spec file generated at: {output_path}")
    return True

if __name__ == "__main__":
    # Use command line argument for output path if provided
    output_path = 'huntarr.spec'
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    success = generate_spec_file(output_path)
    sys.exit(0 if success else 1)
