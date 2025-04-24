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
 
| Application | Status        |
| :---------- | :------------ |
| Sonarr      | **✅ Ready**  |
| Radarr      | **✅ Ready**  |
| Lidarr      | **❌ Not Ready** |
| Readarr     | **❌ Not Ready** |

## Table of Contents
- [Overview](#overview)
- [Other Projects](#other-projects)
- [PayPal Donations – For My Daughter's College Fund](#paypal-donations--for-my-daughters-college-fund)
- [Indexers Approving of Huntarr](#indexers-approving-of-huntarr)
- [How It Works](#how-it-works)
- [Web Interface](#web-interface)
  - [How to Access](#how-to-access)
  - [Web UI Settings](#web-ui-settings)
  - [Volume Mapping](#volume-mapping)
- [Installation Methods](#installation-methods)
  - [Docker Run](#docker-run)
  - [Docker Compose](#docker-compose)
  - [Unraid Users](#unraid-users)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Overview

This application continually searches your media libraries for missing content and items that need quality upgrades. It automatically triggers searches for both missing items and those below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your media collection with the best available quality.

For detailed documentation, please visit our [Wiki](https://github.com/plexguide/Huntarr/wiki).

## Other Projects

* [Legacy Huntarr - Radarr Edition](https://github.com/plexguide/Radarr-Hunter) - Sister version for Movies
* [Current Huntarr - Lidarr Edition](https://github.com/plexguide/Lidarr-Hunter) - Sister version for Music
* [Current Huntarr - Readarr Edition](https://github.com/plexguide/Huntarr-Readarr) - Sister version for Books
* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

<p align="center">
  Join the community on Discord!
  <br>
  <a href="https://discord.gg/VQbZCGzQsn" target="_blank">
    <img src="frontend/static/images/discord.png" alt="Discord" width="48" height="48">
  </a>
</p>

## PayPal Donations – For My Daughter's College Fund

My 12-year-old daughter is passionate about singing, dancing, and exploring STEM. She consistently earns A-B honors! Every donation goes directly into her college fund!

[![Donate with PayPal button](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

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

## Web Interface

Huntarr includes a real-time log viewer and settings management web interface that allows you to monitor and configure its operation directly from your browser.

<table>
  <tr>
    <td colspan="2"> 
      <img width="100%" alt="image" src="https://github.com/user-attachments/assets/438e2013-2a54-4cf2-8418-63b0c6124730" />
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
      <img width="930" alt="image" src="https://github.com/user-attachments/assets/b94d6306-a478-40ab-9aab-cb2f5b02a1fd" />
      <p align="center"><em>Settings UI</em></p>
    </td>
  </tr>
</table>

### Volume Mapping

To ensure data persistence, make sure you map the `/config` directory to a persistent volume on your host system:

```bash
-v /your-path/appdata/huntarr:/config
```

---

## Installation Methods

### Docker Run

The simplest way to run Huntarr is via Docker (all configuration is done via the web UI):

```bash
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /your-path/huntarr:/config \
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
      - /your-path/huntarr:/config
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
## Tips

- **First-Time Setup**: Navigate to the web interface after installation to create your admin account with 2FA option
- **API Connections**: Configure connections to your *Arr applications through the dedicated settings pages
- **Search Frequency**: Adjust Sleep Duration (default: 900 seconds) based on your indexer's rate limits.
- **Batch Processing**: Set Hunt Missing and Upgrade values to control how many items are processed per cycle
- **Queue Management**: Use Minimum Download Queue Size to pause searching when downloads are backed up
- **Skip Processing**: Enable Skip Series/Movie Refresh to significantly reduce disk I/O and database load
- **Future Content**: Keep Skip Future Items enabled to avoid searching for unreleased content
- **Authentication**: Enable two-factor authentication for additional security on your Huntarr instance

## Troubleshooting

- **API Connection Issues**: Verify your API key and URL in the Settings page (check for missing http:// or https://)
- **Authentication Problems**: If you forget your password, delete `/config/user/credentials.json` and restart
- **Two-Factor Authentication**: If locked out of 2FA, remove credentials file to reset your account
- **Web Interface Not Loading**: Confirm port 9705 is correctly mapped and not blocked by firewalls
- **Logs Not Showing**: Check permissions on the `/config/logs/` directory inside your container
- **Missing State Data**: State files in `/config/stateful/` track processed items; verify permissions
- **Docker Volume Issues**: Ensure your volume mount for `/config` has correct permissions and ownership
- **Command Timeouts**: Adjust command_wait_attempts and command_wait_delay in advanced settings
- **Debug Information**: Enable Debug Mode temporarily to see detailed API responses in the logs

**Change Log:**
Visit: https://github.com/plexguide/Huntarr/releases/