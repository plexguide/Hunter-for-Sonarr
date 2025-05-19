#!/usr/bin/env python3
"""
Windows Build Script for Huntarr
This script is the main entry point for building Windows packages
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import the build module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the build module
try:
    from build import build_exe, build_installer, clean
except ImportError:
    print("Error: Could not import build module. Make sure it's in the same directory.")
    sys.exit(1)

def main():
    """Main entry point for Windows build script"""
    parser = argparse.ArgumentParser(
        description="Build Huntarr for Windows",
        epilog="Example: python main.py --exe-only"
    )
    
    parser.add_argument("--clean", action="store_true", help="Clean up build artifacts")
    parser.add_argument("--exe-only", action="store_true", help="Build only the executable, not the installer")
    parser.add_argument("--installer-only", action="store_true", help="Build only the installer, assuming executable is already built")
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
        if not (args.exe_only or args.installer_only):
            return 0
    
    if args.installer_only:
        build_installer()
    elif args.exe_only:
        build_exe()
    else:
        # Build both
        if build_exe():
            build_installer()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
