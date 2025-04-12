#!/usr/bin/env python3
"""
Migration script to replace old UI with new UI
This script will:
1. Create backups of old files
2. Move new UI files to standard locations
3. Clean up by removing "new-" files (optional)
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
    
    # Files to migrate: source -> destination
    files_to_migrate = {
        'templates/new-index.html': 'templates/index.html',
        'templates/new-user.html': 'templates/user.html',
        'static/css/new-style.css': 'static/css/style.css',
        'static/js/new-main.js': 'static/js/main.js',
        'static/js/new-user.js': 'static/js/user.js'
    }
    
    # Check if new UI files exist
    missing_files = []
    for src_file in files_to_migrate.keys():
        if not os.path.exists(os.path.join(base_dir, src_file)):
            missing_files.append(src_file)
    
    if missing_files:
        print("Error: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease make sure all new UI files are in place before running this script.")
        sys.exit(1)
    
    # Create backups and migrate files
    print("Starting UI migration...")
    
    for src_file, dest_file in files_to_migrate.items():
        src_path = os.path.join(base_dir, src_file)
        dest_path = os.path.join(base_dir, dest_file)
        
        # Backup destination file if it exists
        if os.path.exists(dest_path):
            backup_file(dest_path)
        
        # Copy the new file to the destination
        shutil.copy2(src_path, dest_path)
        print(f"Migrated: {src_file} -> {dest_file}")
    
    # Ask about removing the original "new-" files
    print("\nMigration completed successfully!")
    print("The new UI is now the default UI for Huntarr.")
    
    remove_originals = input("\nWould you like to remove the original 'new-' files? (y/n): ").lower()
    if remove_originals == 'y' or remove_originals == 'yes':
        for src_file in files_to_migrate.keys():
            src_path = os.path.join(base_dir, src_file)
            try:
                os.remove(src_path)
                print(f"Removed: {src_file}")
            except Exception as e:
                print(f"Could not remove {src_file}: {e}")
        print("\nCleanup completed. All 'new-' files have been removed.")
    else:
        print("\nOriginal 'new-' files have been kept. You can manually remove them later if needed.")
    
    # Update app.py routes if needed
    app_py_path = os.path.join(base_dir, 'app.py')
    if os.path.exists(app_py_path):
        print("\nNOTE: You may need to update routes in app.py to remove any '/new' routes.")
        print("The standard routes (/, /user) should now point to the new UI files.")

if __name__ == "__main__":
    main()
