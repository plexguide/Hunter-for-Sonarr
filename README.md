<h2 align="center">Huntarr - Find Missing & Upgrade Media Items</h2> 

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr Logo" width="100" height="100">
</p>

---

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2> 

<table>
  <tr>
    <td colspan="2"><img src="https://github.com/user-attachments/assets/34264f2e-928d-44e5-adb7-0dbd08fadfd0" width="100%"/></td>
  </tr>
</table>
 
* Sonarr [Good]
* Radarr [Good]
* Lidarr [Not Ready]
* Readarr [Not Ready]

## WARNING

This uses a new repo `huntarr\huntarr` and does not utilize the env variable and requires the UI. Please read the documentation.

**Change Log:**
Visit: https://github.com/plexguide/Huntarr/releases/

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
- [Use Cases](#use-cases)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Overview

This application continually searches your media libraries for missing content and items that need quality upgrades. It automatically triggers searches for both missing items and those below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your media collection with the best available quality.

For detailed documentation, please visit our [Wiki](https://github.com/plexguide/Huntarr/wiki).

## Other Projects

* [Legacy Huntarr - Radarr Edition](https://github.com/plexguide/Radarr-Hunter) - Sister version for Movies
* [Huntarr - Lidarr Edition](https://github.com/plexguide/Lidarr-Hunter) - Sister version for Music
* [Huntarr - Readarr Edition](https://github.com/plexguide/Huntarr-Readarr) - Sister version for Books
* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

## PayPal Donations – Building My Daughter's Future

My 12-year-old daughter is passionate about singing, dancing, and exploring STEM. She consistently earns A-B honors and school citizenship awards! Every donation goes directly into her college fund. Thank you for your generous support!

[![Donate with PayPal button](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

## Useful Features

🚀 **24/7 Background Operation** - Silently enhances your media library while respecting indexer rate limits
🎯 **Complete Media Management** - Automatically hunts for both missing content and quality upgrades in one solution
🔄 **True State Persistence** - Maintains progress across container restarts with persistent configuration
🛡️ **Indexer Protection** - Customizable batch sizes, timing controls, and rate limiting keep your indexers happy
🌐 **Modern Web Dashboard** - Intuitive interface with real-time colored logs and instant settings management
💾 **Resource Optimization** - Skip metadata refreshes to dramatically reduce disk I/O on your media server
🔮 **Smart Content Handling** - Skips unreleased content and offers independent randomization for efficient processing
🧩 **Multi-Application Support** - Single interface manages Sonarr, Radarr, Lidarr, and Readarr (unified platform)
🔒 **Secure User System** - User authentication with optional two-factor protection for your media automation
⚙️ **Advanced Customization** - Fine-tune every aspect from search intervals to automatic state reset timing

## Indexers Approving of Huntarr:
* https://ninjacentral.co.za

## How It Works

### 🔄 Continuous Automation Cycle

<table>
  <tr>
    <td width="10%" align="center"><h3>1️⃣</h3></td>
    <td width="90%">
      <h3>Connect & Analyze</h3>
      <p>Huntarr connects to your Sonarr/Radarr/Lidarr/Readarr instance and analyzes your media library to identify both missing content and potential quality upgrades.</p>
    </td>
  </tr>
  <tr>
    <td align="center"><h3>2️⃣</h3></td>
    <td>
      <h3>Hunt Missing Content</h3>
      <ul>
        <li>📊 <strong>Smart Selection:</strong> Choose between random or sequential processing</li>
        <li>🔍 <strong>Efficient Refreshing:</strong> Optionally skip metadata refresh to reduce disk I/O</li>
        <li>🔮 <strong>Future-Aware:</strong> Automatically skip content with future release dates</li>
        <li>🎯 <strong>Precise Control:</strong> Set exactly how many items to process per cycle</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td align="center"><h3>3️⃣</h3></td>
    <td>
      <h3>Hunt Quality Upgrades</h3>
      <ul>
        <li>⬆️ <strong>Quality Improvement:</strong> Find content below your quality cutoff settings</li>
        <li>📦 <strong>Batch Processing:</strong> Configure exactly how many upgrades to process at once</li>
        <li>📚 <strong>Large Library Support:</strong> Smart pagination handles even massive libraries</li>
        <li>🔀 <strong>Flexible Modes:</strong> Choose between random or sequential processing</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td align="center"><h3>4️⃣</h3></td>
    <td>
      <h3>State Management</h3>
      <ul>
        <li>📝 <strong>History Tracking:</strong> Remembers which items have been processed</li>
        <li>💾 <strong>Persistent Storage:</strong> State data is saved in the <code>/config</code> directory</li>
        <li>⏱️ <strong>Automatic Reset:</strong> State is cleared after your configured time period (default: 7 days)</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td align="center"><h3>5️⃣</h3></td>
    <td>
      <h3>Repeat & Rest</h3>
      <p>Huntarr waits for your configured interval (adjustable in settings) before starting the next cycle. This ensures your indexers aren't overloaded while maintaining continuous improvement of your library.</p>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/d758b9ae-ecef-4056-ba4e-a7fe363bd182" width="100%"/>
      <p align="center"><em>Missing Content Demo</em></p>
    </td>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/923033d5-fb86-4777-952f-638d8503f776" width="100%"/>
      <p align="center"><em>Quality Upgrade Demo</em></p>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <img src="https://github.com/user-attachments/assets/3e95f6d5-4a96-4bb8-a5b9-1d7b871ff94a" width="100%"/>
      <p align="center"><em>State Management System</em></p>
    </td>
  </tr>
</table>

## Web Interface

Huntarr includes a real-time log viewer and settings management web interface that allows you to monitor and configure its operation directly from your browser.

<table>
  <tr>
    <td colspan="2"> 
      <img width="100%" alt="image" src="https://github.com/user-attachments/assets/a076ea7e-9a7a-4e9b-a631-fa672068851d" />
      <p align="center"><em>Logger UI</em></p>
    </td>
  </tr>
</table>

### How to Access

The web interface is available on port 9705. Simply navigate to:

```
http://YOUR_SERVER_IP:9705
```

The URL will be displayed in the logs when Huntarr starts, using the same hostname you configured for your API_URL.

### Web UI Settings

The web interface allows you to configure all of Huntarr's settings:

<table>
  <tr>
    <td colspan="2"> 
      <img width="930" alt="image" src="https://github.com/user-attachments/assets/19aa9f3c-7641-4b82-8867-22ca2e47536b" />
      <p align="center"><em>Settings UI</em></p>
    </td>
  </tr>
</table>

All settings are now configured entirely through the web UI after initial setup.

## Persistent Storage

Huntarr stores all its configuration and state information in persistent storage, ensuring your settings and processed state are maintained across container restarts and updates.

### Storage Locations

The following directories are used for persistent storage:

- `/config/settings/` - Contains configuration settings (huntarr.json)
- `/config/stateful/` - Contains the state tracking files for processed items
- `/config/user/` - Contains user authentication information

### Data Persistence

All data in these directories is maintained across container restarts. This means:

1. Your settings configured via the web UI will be preserved
2. The list of items that have already been processed will be maintained
3. After a container update or restart, Huntarr will continue from where it left off

### Volume Mapping

To ensure data persistence, make sure you map the `/config` directory to a persistent volume on your host system:

```bash
-v /mnt/user/appdata/huntarr:/config
```

This mapping is included in all of the installation examples below.

---

## Installation Methods

### Docker Run

The simplest way to run Huntarr is via Docker (all configuration is done via the web UI):

```bash
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /mnt/user/appdata/huntarr:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
```

To check on the status of the program, you can use the web interface at http://YOUR_SERVER_IP:9705 or check the logs with:
```bash
docker logs huntarr
```

### Docker Compose

For those who prefer Docker Compose, add this to your `docker-compose.yml` file:

```yaml
services:
  huntarr:
    image: huntarr/huntarr:latest
    container_name: huntarr
    restart: always
    ports:
      - "9705:9705"
    volumes:
      - /mnt/user/appdata/huntarr:/config
    environment:
      - TZ=America/New_York
```

Then run:

```bash
docker-compose up -d huntarr
```

### Unraid Users

Run this from Command Line in Unraid:

```bash
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /mnt/user/appdata/huntarr:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
```

## Use Cases

Huntarr serves multiple purposes in maintaining and enhancing your media collection:

- **Complete Your Library**: Automatically search for and download missing content for your media collection
- **Enhance Media Quality**: Systematically upgrade the quality of your existing content when better versions become available
- **Process New Additions**: When you add new series or movies, Huntarr will automatically start finding the content
- **Efficient Resource Usage**: Runs silently in the background with minimal system resources
- **Smart Content Rotation**: The state tracking system ensures all content gets attention over time, not just recent additions
- **Real-time Monitoring**: Monitor Huntarr's activity through the intuitive web interface
- **Reduce Storage Wear**: Options to skip metadata refreshing help reduce unnecessary disk operations
- **Optimize Searches**: Skip items with future release dates to focus resources on available content
- **Persistent Settings**: Configure once and forget - all settings persist through container updates
- **Continuous Operation**: Maintain state across restarts, picking up right where it left off

## Tips

- **First-Time Setup**: After installation, navigate to the web interface and create your administrator account
- **API Connection**: Configure the connection to your *Arr application through the Settings page
- **Web Interface**: Use the web interface to adjust settings without restarting the container
- **Adjusting Speed**: Lower the Sleep Duration to search more frequently (be careful with indexer limits)
- **Batch Size Control**: Adjust Hunt Missing and Hunt Upgrade values based on your indexer's rate limits
- **Monitored Status**: Set Monitored Only to false if you want to download all missing content regardless of monitored status
- **System Resources**: The application uses minimal resources and can run continuously on even low-powered systems
- **Port Conflicts**: If port 9705 is already in use, map to a different host port (e.g., `-p 8080:9705`)
- **Debugging Issues**: Enable Debug Mode temporarily to see detailed logs when troubleshooting
- **Hard Drive Saving**: Enable Skip Series Refresh to reduce disk activity
- **Search Efficiency**: Keep Skip Future Episodes enabled to avoid searching for unavailable content
- **Persistent Storage**: Make sure to map the `/config` volume to preserve settings and state
- **Dark Mode**: Toggle between light and dark themes in the web interface for comfortable viewing
- **Settings Persistence**: Any settings changed in the web UI are saved immediately and permanently
- **Random vs Sequential**: Configure Random Missing and Random Upgrades based on your preference for processing style

## Troubleshooting

- **API Key Issues**: Check that your API key is correct in the Settings page
- **Connection Problems**: Ensure the API URL is accessible from where you're running the application
- **Login Issues**: If you forget your password, you will need to delete the credentials file at `/config/user/credentials.json` and restart the container
- **Web Interface Not Loading**: Make sure port 9705 is exposed in your Docker configuration and not blocked by a firewall
- **Logs**: Check the container logs with `docker logs huntarr` if running in Docker, or check the log files in `/config/logs/` within the container/volume, or use the web interface.
- **Debug Mode**: Enable Debug Mode in the Advanced Settings to see detailed API responses and process flow
- **Settings Not Persisting**: Verify your volume mount for `/config` is configured correctly
- **State Files**: The application stores state in `/config/stateful/` - if something seems stuck, you can try deleting these files
- **Excessive Disk Activity**: If you notice high disk usage, try enabling Skip Series Refresh
- **Configuration Issues**: Settings now require a container restart to take effect - confirm the restart prompt when saving settings
- **Container Restart Required**: When making significant changes to settings, always restart the container when prompted

---

This application helps automate the tedious process of finding missing content and quality upgrades in your media collection, running quietly in the background while respecting your indexers' rate limits.

---

Thanks to: 

* [IntensiveCareCub](https://www.reddit.com/user/IntensiveCareCub/) for the Hunter to Huntarr idea!
* [ZPatten](https://github.com/zpatten) for adding the Queue Size and Delay Commands!
