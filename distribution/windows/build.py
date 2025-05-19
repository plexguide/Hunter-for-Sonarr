#!/usr/bin/env python3
"""
Huntarr Windows Build Script
This script builds the Windows executable and installer for Huntarr.
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Constants
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = SCRIPT_DIR.parent.parent  # Navigate up two directories to project root

def run_command(cmd, cwd=None):
    """Run a command and return the result
    
    Args:
        cmd: Command list to run
        cwd: Current working directory for the command
    
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, cwd=cwd)
    return result.returncode == 0

def build_exe():
    """Build the Windows executable using PyInstaller"""
    print("Building Huntarr Windows executable...")
    
    # Make sure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Make sure all requirements are installed
    run_command([sys.executable, "-m", "pip", "install", "-r", str(ROOT_DIR / "requirements.txt")])
    run_command([sys.executable, "-m", "pip", "install", "pywin32"])
    
    # Build using the spec file
    spec_file = SCRIPT_DIR / "huntarr.spec"
    
    # Make sure we're in the project root directory when running PyInstaller
    # This helps with finding relative paths
    run_command([sys.executable, "-m", "PyInstaller", str(spec_file)], cwd=str(ROOT_DIR))
    
    print("Executable build complete.")
    return True

def build_installer():
    """Build the Windows installer using Inno Setup"""
    print("Building Huntarr Windows installer...")
    
    # Check if Inno Setup is installed
    inno_compiler = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(inno_compiler):
        print(f"ERROR: Inno Setup compiler not found at {inno_compiler}")
        print("Please install Inno Setup 6 from https://jrsoftware.org/isdl.php")
        return False
    
    # Create installer directory if it doesn't exist
    installer_dir = ROOT_DIR / "installer"
    installer_dir.mkdir(exist_ok=True)
    
    # Copy the installer script to the root
    installer_script = SCRIPT_DIR / "installer" / "huntarr_installer.iss"
    target_script = ROOT_DIR / "huntarr_installer.iss"
    shutil.copy2(installer_script, target_script)
    
    # Run the Inno Setup compiler
    run_command([inno_compiler, str(target_script)])
    
    # Clean up
    if target_script.exists():
        target_script.unlink()
    
    print("Installer build complete.")
    return True

def clean():
    """Clean up build artifacts"""
    print("Cleaning up build artifacts...")
    
    # Remove PyInstaller build directories
    build_dir = ROOT_DIR / "build"
    dist_dir = ROOT_DIR / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Remove any .spec files in the root directory
    for spec_file in ROOT_DIR.glob("*.spec"):
        spec_file.unlink()
    
    print("Cleanup complete.")
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build Huntarr for Windows")
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
