# Huntarr Windows Installer

This directory contains the tools and configuration needed to build a Windows installer for Huntarr.

## Requirements

To build the Huntarr Windows installer, you need:

1. **Python 3.8+** - Required for the application and build scripts
2. **PyInstaller** - Used to bundle Huntarr as a Windows executable
   - Install with `pip install pyinstaller`
3. **NSIS (Nullsoft Scriptable Install System)** - Used to create the Windows installer
   - Download from [NSIS](https://nsis.sourceforge.io/Download)
   - Make sure `makensis` is available in your PATH
4. **pywin32** - Required for Windows service support
   - Install with `pip install pywin32`

## Building the Installer

### Automated Build

The easiest way to build the installer is using the automated build script:

```bash
# Navigate to the Huntarr project root
cd /path/to/Huntarr.io

# Run the build script
python installer/build_windows_installer.py
```

This will:
1. Read the current version from `version.txt`
2. Update the NSIS installer script to match the version
3. Build the executable using PyInstaller
4. Create the installer using NSIS

The installer will be created in the project root directory as `Huntarr-Setup-x.y.z.exe`.

### Manual Build

If you prefer to build manually:

1. **Build the executable**:
   ```bash
   cd /path/to/Huntarr.io
   pyinstaller huntarr.spec
   ```

2. **Build the installer**:
   ```bash
   cd /path/to/Huntarr.io
   makensis installer/huntarr-installer.nsi
   ```

## Windows Service Support

The Huntarr Windows installer includes support for running Huntarr as a Windows service. This allows Huntarr to run in the background without requiring a user to be logged in.

To manage the Huntarr service:

- **Install service**: `Huntarr.exe --install-service`
- **Remove service**: `Huntarr.exe --remove-service`
- **Start service**: `Huntarr.exe --start`
- **Stop service**: `Huntarr.exe --stop`
- **Restart service**: `Huntarr.exe --restart`
- **Update service**: `Huntarr.exe --update`
- **Run as service in debug mode**: `Huntarr.exe --debug`

## Installer Options

The Windows installer provides the following options during installation:

1. **Huntarr Core** (Required) - Installs the core application
2. **Windows Service** - Installs and configures Huntarr to run as a Windows service
3. **Desktop Shortcut** - Creates a desktop shortcut for Huntarr

## Troubleshooting

If you encounter issues with the Windows service:

1. Check the Windows Event Viewer for service-related errors
2. Look for logs in the `config/logs/windows_service.log` file
3. Try running Huntarr directly (not as a service) to check for application errors

## Updating the Installer

When updating the Huntarr version:

1. Update the version in the `version.txt` file
2. The build script will automatically update the NSIS installer script

## Distribution

After building the installer:

1. Test it thoroughly on a Windows machine
2. Include it with your GitHub release
3. Document any Windows-specific information in the release notes
