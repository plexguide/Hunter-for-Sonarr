# Huntarr.spec - PyInstaller specification file

# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Assuming main.py is at the project root
main_script = 'main.py'

# Collect data files (static assets, templates)
# (source_path_relative_to_spec_file, destination_path_in_bundle)
datas = []
data_directories_to_bundle = [
    ('frontend/static', 'frontend/static'),
    ('frontend/templates', 'frontend/templates'),
    # Add other directories like 'config_examples' if needed:
    # ('config_examples', 'config_examples')
]

for src_dir, dest_dir in data_directories_to_bundle:
    if os.path.exists(src_dir):
        datas.append((src_dir, dest_dir))
    else:
        print(f"Warning: Data directory '{src_dir}' not found and will not be bundled.", file=sys.stderr)

# Example: Add a specific file if needed
# if os.path.exists('some_other_data_file.json'):
#    datas.append(('some_other_data_file.json', '.'))


a = Analysis(
    [main_script],
    pathex=[os.path.dirname(os.path.abspath(__file__))], # Ensure project root is in path
    binaries=[],
    datas=datas,
    hiddenimports=[], # Add any modules PyInstaller might miss here
    hookspath=[],
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
    [], # Explicitly no binaries for the exe component itself
    name='Huntarr', # Name of the output .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Compresses the executable; requires UPX to be installed in build environment
    upx_exclude=[],
    runtime_tmpdir=None, # None means use system default temp
    console=True, # True for a console application, False for a GUI (no console window on start)
    # icon='path/to/your/app_icon.ico' # Specify your application icon here
)

# For a one-folder bundle (output will be in dist/Huntarr/)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Huntarr' # This will be the name of the folder in 'dist'
)
