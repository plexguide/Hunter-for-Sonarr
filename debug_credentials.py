#!/usr/bin/env python3
"""
Debug utility to check credentials.json file
"""

import os
import json
import pathlib

# User directory setup - same as in auth.py
USER_DIR = pathlib.Path("/config/user")
USER_FILE = USER_DIR / "credentials.json"

def check_credentials_file():
    """Check if credentials.json exists and is readable"""
    print(f"\nChecking credentials file at: {USER_FILE}")
    
    if not USER_DIR.exists():
        print(f"ERROR: User directory does not exist: {USER_DIR}")
        return False

    if not USER_FILE.exists():
        print(f"ERROR: Credentials file does not exist: {USER_FILE}")
        return False
    
    print(f"✓ Found credentials file: {USER_FILE}")
    
    try:
        # Check file size
        file_size = os.path.getsize(USER_FILE)
        print(f"✓ File size: {file_size} bytes")
        
        if file_size == 0:
            print("ERROR: Credentials file is empty")
            return False
        
        # Check file permissions
        permissions = oct(os.stat(USER_FILE).st_mode)[-3:]
        print(f"✓ File permissions: {permissions}")
        
        # Try to read the file
        with open(USER_FILE, 'r') as f:
            data = json.load(f)
            
        # Check required fields
        required_fields = ["username", "password", "created_at"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"ERROR: Missing fields in credentials file: {', '.join(missing_fields)}")
            return False
            
        print("✓ Credentials file format looks correct")
        print(f"✓ Contains username hash: {data['username'][:10]}...")
        return True
    except json.JSONDecodeError:
        print("ERROR: Credentials file contains invalid JSON")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read credentials file: {e}")
        return False

if __name__ == "__main__":
    check_credentials_file()
