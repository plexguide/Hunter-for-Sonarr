#!/usr/bin/env python3
"""
Migration script to help users switch to the new UI
"""
import os
import shutil
import sys

def backup_file(filepath):
    """Create backup of existing file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup"
        shutil.copy2(filepath, backup_path)
        print(f"Created backup: {backup_path}")
    
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of files to check
    files = [
        'templates/new-index.html',
        'templates/new-user.html',
        'static/css/new-style.css',
        'static/js/new-main.js',
        'static/js/new-user.js'
    ]
    
    # Check if all required files exist
    missing_files = []
    for file in files:
        if not os.path.exists(os.path.join(base_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        print("Error: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease make sure all new UI files are in place before running this script.")
        sys.exit(1)
    
    # Create a config file to enable the new UI by default
    config_file = os.path.join(base_dir, 'config/ui_settings.json')
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w') as f:
        f.write('{"use_new_ui": true}')
    
    print("\nMigration completed successfully!")
    print("The new UI is now enabled by default.")
    print("You can access it at:")
    print("  - Main UI: http://your-server/new")
    print("  - User Settings: http://your-server/user/new")
    print("\nTo return to the old UI temporarily, visit:")
    print("  - http://your-server/?ui=classic")

if __name__ == "__main__":
    main()
