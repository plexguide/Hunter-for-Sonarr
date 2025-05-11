# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Version info for Windows executable
version = os.environ.get('BUILD_VERSION', '1.1.2')
version_tuple = tuple(map(int, version.split('.'))) + (0,) * (4 - len(version.split('.')))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('config', 'config'),
        ('src/primary/default_configs', 'src/primary/default_configs'),
        # Check if static directory exists before including it
        # ('static', 'static'),  # Commented out as it may not exist in all branches
        # These files will be created during the build process
        # ('Huntarr-Windows-README.md', '.'),
        # ('launcher.bat', '.'),
    ],
    hiddenimports=[
        'win32timezone', 
        'waitress',
        'win32api',
        'win32con',
        'win32service',
        'win32serviceutil',
        'src.primary.windows_config',
        'src.primary.windows_launcher',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'webbrowser',
        'requests'
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='frontend/static/img/logo.ico',  # Using path expected by PyInstaller
    version='file_version_info.txt',
    # Embed version info directly
    file_version=version,
    product_version=version,
)
