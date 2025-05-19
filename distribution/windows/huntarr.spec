# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import pathlib
import glob

# Find the project root directory from the spec file location
spec_dir = pathlib.Path(os.path.dirname(os.path.abspath(SPECPATH)))
project_dir = spec_dir.parent.parent  # Go up two levels to project root

# In GitHub Actions, the current working directory is already the project root
# Check if we're in GitHub Actions by looking at the environment
if os.environ.get('GITHUB_ACTIONS'):
    # Use the current directory instead
    project_dir = pathlib.Path(os.getcwd())

# Print current directory and list files for debugging
print(f"Current directory: {os.getcwd()}")
print(f"Project directory: {project_dir}")
print("Files in current directory:")
for file in os.listdir(os.getcwd()):
    print(f"  {file}")

# Find main.py file
main_py_path = project_dir / 'main.py'
if not main_py_path.exists():
    main_py_files = list(glob.glob(f"{project_dir}/**/main.py", recursive=True))
    if main_py_files:
        main_py_path = pathlib.Path(main_py_files[0])
        print(f"Found main.py at: {main_py_path}")
    else:
        print("ERROR: main.py not found!")
        # Use a placeholder that will cause an error with a clearer message
        main_py_path = project_dir / 'main.py'

block_cipher = None

# Create a list of data files to include with absolute paths
datas = [
    (str(project_dir / 'frontend'), 'frontend'),
    (str(project_dir / 'src'), 'src'),
]

# Add tools directory if it exists
if os.path.exists(str(project_dir / 'tools')):
    datas.append((str(project_dir / 'tools'), 'tools'))

# Add assets directory if it exists
if os.path.exists(str(project_dir / 'assets')):
    datas.append((str(project_dir / 'assets'), 'assets'))

a = Analysis(
    [str(main_py_path)],
    pathex=[str(project_dir)],
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
    icon=str(project_dir / 'frontend/static/logo/huntarr.ico'),
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
