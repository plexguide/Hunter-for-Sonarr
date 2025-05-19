# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Create a list of data files to include
datas = [
    ('frontend', 'frontend'),
    ('src', 'src'),
]

# Add tools directory if it exists
if os.path.exists('tools'):
    datas.append(('tools', 'tools'))

# Add assets directory if it exists
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'waitress',
        'pyotp',
        'win32serviceutil',
        'win32service',
        'win32event',
        'servicemanager',
        'win32timezone',
        'pywin32',
        'bcrypt',
        'qrcode',
        'PIL.Image',
        'flask',
        'flask.json',
        'flask.sessions',
        'markupsafe',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.exceptions',
        'itsdangerous',
        'logging.handlers',
        'email',
        'importlib',
        'json',
        'sqlite3',
        'requests',
        'urllib3',
        'certifi',
        'idna',
        'charset_normalizer',
        'queue',
        'threading',
        'socket',
        'datetime',
        'time',
        'os',
        'sys',
        're',
        'winreg',
        'hashlib',
        'base64',
        'uuid',
        'pathlib',
        'concurrent.futures',
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
    [],
    exclude_binaries=True,
    name='Huntarr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='frontend/static/logo/huntarr.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Huntarr',
)
