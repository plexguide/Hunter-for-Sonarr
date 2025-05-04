# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Debug information - will be shown in build logs
print("===== HUNTARR WINDOWS FIXED SPEC EXECUTION =====")
print(f"Current working directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Ensure we have a way to find template paths at runtime
block_cipher = None

# Find the project root directory
project_root = os.path.abspath(os.getcwd())
print(f"Project root: {project_root}")

# Template and static directories
template_dir = os.path.join(project_root, 'frontend', 'templates')
static_dir = os.path.join(project_root, 'frontend', 'static')

print(f"Template directory: {template_dir}")
print(f"Static directory: {static_dir}")

# List of data directories to include
datas = [
    (template_dir, 'templates'),  # Copy templates to top-level templates dir
    (static_dir, 'static'),       # Copy static files to top-level static dir
    (os.path.join(project_root, 'src'), 'src'),
    (os.path.join(project_root, 'requirements.txt'), '.'),
    (os.path.join(project_root, 'version.txt'), '.')
]

# Runtime hook to fix template paths
runtime_hooks = []

# Create a runtime hook to fix the template paths
hook_content = """
import os
import sys

# Detect if we're running from a PyInstaller package
if getattr(sys, 'frozen', False):
    # We're running from the bundled package
    bundle_dir = os.path.dirname(sys.executable)
    print(f"Running from PyInstaller bundle: {bundle_dir}")
    
    # Set environment variables to help Flask find templates
    os.environ['FLASK_TEMPLATE_DIR'] = os.path.join(bundle_dir, 'templates')
    os.environ['FLASK_STATIC_DIR'] = os.path.join(bundle_dir, 'static')
    
    print(f"Set template dir to: {os.environ['FLASK_TEMPLATE_DIR']}")
    print(f"Set static dir to: {os.environ['FLASK_STATIC_DIR']}")
"""

# Write the hook to a file
hook_file = os.path.join(project_root, 'fix_template_paths.py')
with open(hook_file, 'w') as f:
    f.write(hook_content)
    
runtime_hooks.append(hook_file)
print(f"Created runtime hook at: {hook_file}")

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask', 'waitress', 'requests', 'dateutil', 'pyotp', 'qrcode', 'psutil', 'pytz',
        'win32timezone', 'win32serviceutil', 'win32service', 'win32event', 'servicemanager', 'socket',
        'src.primary.windows_service'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
