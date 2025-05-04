#!/usr/bin/env python3
"""
Windows Installer Build Script for Huntarr
This script automates the process of building a Windows installer for Huntarr.
"""

import os
import sys
import shutil
import subprocess
import re
import argparse
from pathlib import Path

# Set up argument parser
parser = argparse.ArgumentParser(description='Build Windows installer for Huntarr')
parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
parser.add_argument('--skip-dist', action='store_true', help='Skip PyInstaller dist build (use existing)')
parser.add_argument('--skip-nsis', action='store_true', help='Skip NSIS installer creation')
args = parser.parse_args()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
print(f"Project root: {PROJECT_ROOT}")

# Directories
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
INSTALLER_DIR = PROJECT_ROOT / "installer"
ASSETS_DIR = PROJECT_ROOT / "assets"

def get_version():
    """Get the current version from version.txt"""
    version_file = PROJECT_ROOT / "version.txt"
    if not version_file.exists():
        print("Error: version.txt not found")
        sys.exit(1)
    
    with open(version_file, 'r') as f:
        version = f.read().strip()
    
    # Validate version format (should be x.y.z)
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"Error: Invalid version format in version.txt: {version}")
        sys.exit(1)
        
    return version

def update_nsis_version(version):
    """Update version in NSIS script to match version.txt"""
    nsis_file = INSTALLER_DIR / "huntarr-installer.nsi"
    if not nsis_file.exists():
        print("Error: NSIS installer script not found")
        sys.exit(1)
    
    with open(nsis_file, 'r') as f:
        content = f.read()
    
    # Parse version components
    major, minor, build = version.split('.')
    
    # Update version in NSIS script
    content = re.sub(r'!define VERSIONMAJOR \d+', f'!define VERSIONMAJOR {major}', content)
    content = re.sub(r'!define VERSIONMINOR \d+', f'!define VERSIONMINOR {minor}', content)
    content = re.sub(r'!define VERSIONBUILD \d+', f'!define VERSIONBUILD {build}', content)
    
    with open(nsis_file, 'w') as f:
        f.write(content)
    
    print(f"Updated NSIS script version to {version}")

def check_requirements():
    """Check if required tools are installed"""
    # Check for PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: PyInstaller not found. Install it with 'pip install pyinstaller'")
        sys.exit(1)
    
    # Check for NSIS
    if not args.skip_nsis:
        try:
            subprocess.run(["makensis", "/VERSION"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: NSIS not found. Please install NSIS from https://nsis.sourceforge.io/")
            sys.exit(1)
    
    print("All required tools are installed.")

def clean_build_dirs():
    """Clean build and dist directories"""
    if args.clean:
        print("Cleaning build directories...")
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)

def build_executable():
    """Build executable using PyInstaller"""
    if args.skip_dist:
        print("Skipping PyInstaller build...")
        return
    
    print("Building executable with PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", "huntarr.spec"],
        cwd=PROJECT_ROOT,
        check=False, 
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error building executable: {result.stderr}")
        sys.exit(1)
    
    print("PyInstaller build successful!")

def build_installer(version):
    """Build installer using NSIS"""
    if args.skip_nsis:
        print("Skipping NSIS installer build...")
        return
    
    print("Building installer with NSIS...")
    nsis_script = INSTALLER_DIR / "huntarr-installer.nsi"
    
    result = subprocess.run(
        ["makensis", str(nsis_script)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error building installer: {result.stderr}")
        sys.exit(1)
    
    installer_file = f"Huntarr-Setup-{version}.exe"
    output_path = PROJECT_ROOT / installer_file
    if output_path.exists():
        print(f"Installer built successfully: {output_path}")
    else:
        print("Warning: Installer file not found at expected location")

def main():
    """Main build process"""
    print("=== Huntarr Windows Installer Build Script ===")
    
    # Get version
    version = get_version()
    print(f"Building Huntarr version {version}")
    
    # Update NSIS version
    update_nsis_version(version)
    
    # Check requirements
    check_requirements()
    
    # Clean build directories if requested
    clean_build_dirs()
    
    # Build executable
    build_executable()
    
    # Build installer
    build_installer(version)
    
    print("=== Build process completed ===")

if __name__ == "__main__":
    main()
