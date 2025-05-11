"""
Huntarr PyInstaller spec file
This file configures PyInstaller to properly bundle Huntarr for Windows as a single executable
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None

# Define the base directory
base_dir = os.path.abspath(os.path.dirname(__file__))

# Define paths for data files
frontend_dir = os.path.join(base_dir, 'frontend')
config_dir = os.path.join(base_dir, 'config')

# Collect all data files
frontend_data = collect_data_files('frontend', include_py_files=True, excludes=['*.pyc', '*.pyo', '__pycache__'])
static_data = [(os.path.join(frontend_dir, 'static', file), os.path.join('frontend', 'static', file)) 
               for file in os.listdir(os.path.join(frontend_dir, 'static'))]
templates_data = [(os.path.join(frontend_dir, 'templates', file), os.path.join('frontend', 'templates', file)) 
                 for file in os.listdir(os.path.join(frontend_dir, 'templates'))]

# Create config directory structure
config_dirs = [
    'config',
    'config/logs',
    'config/db',
    'config/settings'
]

# Create empty directories for config
for dir_path in config_dirs:
    full_path = os.path.join(base_dir, dir_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)

# List of additional data files to include
extra_data = [
    (os.path.join(base_dir, 'README.md'), '.'),
    (config_dir, 'config'),
]

# Combine all data files
datas = frontend_data + static_data + templates_data + extra_data

# Define the analysis for the main executable
a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'win32timezone',
        'win32serviceutil',
        'win32service',
        'win32event',
        'servicemanager',
        'flask',
        'waitress',
        'bcrypt',
        'qrcode',
        'PIL',
        'pyotp',
        'src.primary.windows_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create the PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the main ONE-FILE executable
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(frontend_dir, 'static', 'logo', 'favicon.ico'),
)

# Create the Windows service ONE-FILE executable
service_exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HuntarrService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(frontend_dir, 'static', 'logo', 'favicon.ico'),
)
