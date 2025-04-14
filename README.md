<h2 align="center">Huntarr Sonarr - Find Missing & Upgrade TV Shows</h2> 

<p align="center">
  <img src="https://github.com/plexguide/Huntarr-Sonarr/blob/main/logo/128.png?raw=true" alt="Huntarr Logo" width="100" height="100">
</p>

---

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2> 

<table>
  <tr>
    <td colspan="2"><img src="https://github.com/user-attachments/assets/34264f2e-928d-44e5-adb7-0dbd08fadfd0" width="100%"/></td>
  </tr>
</table>
 
**NOTE**: This is a Sonarr-only specialized version of Huntarr. If making changes in the UI do not appear to take effect after saving, type: `docker restart huntarr-sonarr`

## WARNING

This uses a new repo and does not utilize the env variable and requires the UI. Please read the documentation.

**Change Log:**
Visit: https://github.com/plexguide/Huntarr-Sonarr/releases/

## Table of Contents
- [Overview](#overview)
- [Related Projects](#related-projects)
- [Features](#features)
- [How It Works](#how-it-works)
- [Web Interface](#web-interface)
- [Persistent Storage](#persistent-storage)
- [Installation Methods](#installation-methods)
  - [Docker Run](#docker-run)
  - [Docker Compose](#docker-compose)
  - [Unraid Users](#unraid-users)
  - [SystemD Service](#systemd-service)
- [Use Cases](#use-cases)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Overview

Huntarr Sonarr Edition continually searches your TV series libraries for missing episodes and shows that need quality upgrades. It automatically triggers searches for both missing content and episodes below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your TV show collection with the best available quality.

For detailed documentation, please visit our [Wiki](https://github.com/plexguide/Huntarr-Sonarr/wiki).

## Related Projects

* [Huntarr - Main Edition](https://github.com/plexguide/Huntarr) - The full-featured Huntarr supporting multiple *Arr apps
* [Huntarr - Radarr Edition](https://github.com/plexguide/Radarr-Hunter) - Sister version for Movies
* [Huntarr - Lidarr Edition](https://github.com/plexguide/Lidarr-Hunter) - Sister version for Music
* [Huntarr - Readarr Edition](https://github.com/plexguide/Huntarr-Readarr) - Sister version for Books
* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

## PayPal Donations – Building My Daughter's Future

My 12-year-old daughter is passionate about singing, dancing, and exploring STEM. She consistently earns A-B honors and dreams of a bright future. Every donation goes directly into her college fund, helping turn those dreams into reality. Thank you for your generous support!

[![Donate with PayPal button](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

## Features

- 🔄 **Continuous Operation**: Runs indefinitely until manually stopped
- 🎯 **Dual Targeting System**: Targets both missing items and quality upgrades
- 🎲 **Separate Random Controls**: Separate toggles for random missing content and random upgrades
- ⏱️ **Throttled Searches**: Includes configurable delays to prevent overloading indexers
- 📊 **Status Reporting**: Provides clear feedback about what it's doing and which items it's searching for
- 🛡️ **Error Handling**: Gracefully handles connection issues and API failures
- 🔁 **State Tracking**: Keeps track of what has been searched and what still needs to be found

## Tips

- **First-Time Setup**: After installation, navigate to the web interface and configure your Sonarr connection
- **API Connection**: Configure the connection to your Sonarr server through the Settings page
- **Web Interface**: Use the web interface to adjust settings without restarting the container
- **Adjusting Speed**: Lower the Sleep Duration to search more frequently (be careful with indexer limits)
- **Batch Size Control**: Adjust Hunt Missing Shows and Hunt Upgrade Episodes values based on your indexer's rate limits
- **Monitored Status**: Set Monitored Only to false if you want to download all missing episodes regardless of monitored status
- **System Resources**: The application uses minimal resources and can run continuously on even low-powered systems
- **Port Conflicts**: If port 9705 is already in use, map to a different host port (e.g., `-p 8080:9705`)
- **Debugging Issues**: Enable Debug Mode temporarily to see detailed logs when troubleshooting
- **Hard Drive Saving**: Enable Skip Series Refresh to reduce disk activity
- **Search Efficiency**: Keep Skip Future Episodes enabled to avoid searching for unavailable episodes
- **Persistent Storage**: Make sure to map the `/config` volume to preserve settings and state
- **Dark Mode**: Toggle between light and dark themes in the web interface for comfortable viewing
- **Settings Persistence**: Any settings changed in the web UI are saved immediately and permanently
- **Random vs Sequential**: Configure Random Missing and Random Upgrades based on your preference for processing style

## Troubleshooting

- **API Key Issues**: Check that your Sonarr API key is correct in the Settings page
- **Connection Problems**: Ensure the Sonarr API URL is accessible from where you're running the application
- **Login Issues**: If you forget your password, you will need to delete the credentials file at `/config/user/credentials.json` and restart the container
- **Web Interface Not Loading**: Make sure port 9705 is exposed in your Docker configuration and not blocked by a firewall
- **Logs**: Check the container logs with `docker logs huntarr-sonarr` if running in Docker, or use the web interface
- **Debug Mode**: Enable Debug Mode in the Advanced Settings to see detailed API responses and process flow
- **Settings Not Persisting**: Verify your volume mount for `/config` is configured correctly
- **State Files**: The application stores state in `/config/stateful/` - if something seems stuck, you can try deleting these files
- **Excessive Disk Activity**: If you notice high disk usage, try enabling Skip Series Refresh
- **Configuration Issues**: Settings now require a container restart to take effect - confirm the restart prompt when saving settings
- **Container Restart Required**: When making significant changes to settings, always restart the container when prompted

---

This specialized Sonarr edition helps automate the tedious process of finding missing episodes and quality upgrades in your TV show collection, running quietly in the background while respecting your indexers' rate limits.

---

Thanks to: 

* [IntensiveCareCub](https://www.reddit.com/user/IntensiveCareCub/) for the Hunter to Huntarr idea!
* [ZPatten](https://github.com/zpatten) for adding the Queue Size and Delay Commands!
* The Huntarr community for continued support and feedback!
