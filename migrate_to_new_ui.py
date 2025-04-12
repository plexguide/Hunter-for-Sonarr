#!/usr/bin/env python3
"""
Migration script to move from old UI to new UI
This script will:
1. Create backups of old files
2. Move new files to standard locations
3. Clean up unused files
"""
import os
import shutil
from pathlib import Path

# Define base directory
BASE_DIR = Path(__file__).parent

# Files to be replaced
FILES_TO_REPLACE = {
    'templates/new-index.html': 'templates/index.html',
    'templates/new-user.html': 'templates/user.html',
    'static/css/new-style.css': 'static/css/style.css',
    'static/js/new-main.js': 'static/js/main.js',
    'static/js/new-user.js': 'static/js/user.js'
}

def create_backup(filepath):
    """Create backup of an existing file"""
    full_path = BASE_DIR / filepath
    if full_path.exists():
        backup_path = full_path.with_suffix(full_path.suffix + '.bak')
        shutil.copy2(full_path, backup_path)
        print(f"Created backup: {backup_path}")

def replace_file(src, dest):
    """Replace destination file with source file"""
    src_path = BASE_DIR / src
    dest_path = BASE_DIR / dest
    
    if not src_path.exists():
        print(f"Error: Source file {src_path} doesn't exist")
        return False
    
    create_backup(dest)
    
    # Copy the file
    shutil.copy2(src_path, dest_path)
    print(f"Replaced {dest} with {src}")
    return True

def main():
    print("Starting UI migration...")
    
    # Create backups and replace files
    for src, dest in FILES_TO_REPLACE.items():
        replace_file(src, dest)
    
    print("\nMigration completed successfully!")
    print("The new UI is now the default UI.")
    
    # Cleanup instructions
    print("\nYou may now delete the following files if desired:")
    for src in FILES_TO_REPLACE:
        print(f"  - {BASE_DIR / src}")
    
    print("\nTo keep the old UI files as backups, rename them (e.g., .old extension)")
    print("Example: mv templates/new-index.html templates/new-index.html.old")

if __name__ == "__main__":
    main()
