#!/bin/bash
set -e

echo "Starting Huntarr-Sonarr"
echo "----------------------"

# Install Python dependencies
pip install --no-cache-dir -r /scripts/requirements.txt

# Make the main script executable
chmod +x /scripts/huntarr-sonarr.py

# Create a symbolic link for the command
ln -sf /scripts/huntarr-sonarr.py /usr/local/bin/huntarr-sonarr

# Make it executable
chmod +x /usr/local/bin/huntarr-sonarr

# Run the application
exec python /scripts/huntarr-sonarr.py