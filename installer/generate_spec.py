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
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current working directory
cwd = os.getcwd()

# Ensure paths are correct for the GitHub Actions environment
a = Analysis(
    ['main.py'],
    pathex=[cwd],
    binaries=[],
    datas=[
        (os.path.join(cwd, 'src'), 'src'),
        (os.path.join(cwd, 'templates'), 'templates'),
        (os.path.join(cwd, 'static'), 'static'),
        (os.path.join(cwd, 'requirements.txt'), '.'),
        (os.path.join(cwd, 'version.txt'), '.'),
        (os.path.join(cwd, 'assets'), 'assets'),
    ],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(cwd, 'assets', 'huntarr.ico')
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
