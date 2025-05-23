<h2 align="center">Huntarr - Find Missing & Upgrade Media Items</h2> 

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr Logo" width="100" height="100">
</p>

---

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2> 

<img src="https://github.com/user-attachments/assets/1ea6ca9c-0909-4b6a-b573-f778b65af8b2" width="100%"/>
 
| Application | Status        |
| :---------- | :------------ |
| Sonarr      | **✅ Ready**  |
| Radarr      | **✅ Ready**  |
| Lidarr      | **✅ Ready**  |
| Readarr     | **✅ Ready**  |
| Whisparr v2 | **✅ Ready**  |
| Whisparr v3 | **✅ Ready**  |
| Bazarr    | **❌ Not Ready** | 


Keep in mind this is very early in program development. If you have a very special hand picked collection (because some users are extra special), test before you deploy.

## Table of Contents
- [Overview](#overview)
- [Other Projects](#other-projects)
- [Community](#community)
- [Indexers Approving of Huntarr](#indexers-approving-of-huntarr)
- [Installation Methods](#installation-methods)
- [How It Works](#how-it-works)
- [Web Interface](#web-interface)
  - [How to Access](#how-to-access)
  - [Web UI Settings](#web-ui-settings)
  - [Volume Mapping](#volume-mapping)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)
- [Change Log](#change-log)

## Overview

This application continually searches your media libraries for missing content and items that need quality upgrades. It automatically triggers searches for both missing items and those below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your media collection with the best available quality.

For detailed documentation, please visit our <a href="https://plexguide.github.io/Huntarr.io/" target="_blank" rel="noopener noreferrer">Wiki</a>.

## Other Projects

* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

## Community

<p align="center">
  Join the community on Discord!
  <br>
  <a href="https://discord.com/invite/PGJJjR5Cww" target="_blank">
    <img src="frontend/static/images/discord.png" alt="Discord" width="48" height="48">
  </a>
</p>

## PayPal Donations – For My Daughter's College Fund

My 12-year-old daughter is passionate about singing, dancing, and exploring STEM. She consistently earns A-B honors! Every donation goes directly into her college fund!

[![Donate with PayPal button](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

## Indexers Approving of Huntarr:
* https://ninjacentral.co.za

## Installation Methods

🐋 **[Docker Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html)**
🪟 **[Windows Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#windows-installation)**
🍏 **[macOS Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#macos-installation)**
🔵 **[Unraid Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#unraid-installation)**
🔧 **[Alternative Methods](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#alternative-methods)**

Special thanks to [Nwithan8](https://github.com/nwithan8) for maintaining the Unraid templates and helping Huntarr grow through the Unraid Community Applications repository.

## How It Works

### 🔄 Continuous Automation Cycle

#### 1️⃣ Connect & Analyze
🔌 Huntarr connects to your Sonarr/Radarr/Lidarr/Readarr/Whisparr/Eros instances and analyzes your media libraries to identify both missing content and potential quality upgrades.

#### 2️⃣ Hunt Missing Content
- 🔍 **Efficient Refreshing:** Skip metadata refresh to reduce disk I/O and database load
- 🔮 **Future-Aware:** Automatically skip content with future release dates
- 🎯 **Precise Control:** Configure exactly how many items to process per cycle
- 👀 **Monitored Only:** Focus only on content you've marked as monitored

#### 3️⃣ Hunt Quality Upgrades
- ⬆️ **Quality Improvement:** Find content below your quality cutoff settings
- 📦 **Batch Processing:** Set specific numbers of upgrades to process per cycle
- 🚦 **Queue Management:** Automatically pauses when download queue exceeds your threshold
- ⏱️ **Command Monitoring:** Waits for commands to complete with consistent timeouts

#### 4️⃣ API Management
- 🛡️ **Rate Protection:** Hourly caps prevent overloading your indexers
- ⏲️ **Universal Timeouts:** Consistent API timeouts (120s) across all applications
- 🔄 **Consistent Headers:** Identifies as Huntarr to all Arr applications
- 📊 **Intelligent Monitoring:** Visual indicators show API usage limits

#### 5️⃣ Repeat & Rest
💤 Huntarr waits for your configured interval (adjustable in settings) before starting the next cycle, ensuring your indexers aren't overloaded while maintaining continuous improvement of your library.

## Web Interface

Huntarr's live homepage will provide you statics about how many hunts have been pursed regarding missing media and upgrade searches! Note: Numbers reflected are but all required for testing. 

<p align="center">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/1ffeb7f1-7dec-484c-9073-02d460953f99" />
  <br>
  <em>Homepage</em>
</p>

Huntarr includes a real-time log viewer and settings management web interface that allows you to monitor and configure its operation directly from your browser.

<p align="center">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/93c1a5d3-e82a-416a-8d41-0379ea221d7a" />
  <br>
  <em>Logger UI</em>
</p>

### How to Access

The web interface is available on port 9705. Simply navigate to:

```
http://YOUR_SERVER_IP:9705
```

The URL will be displayed in the logs when Huntarr starts, using the same hostname you configured for your API_URL.

### Web UI Settings

The web interface allows you to configure all of Huntarr's settings:

<p align="center">
  <img width="930" alt="image" src="https://github.com/user-attachments/assets/e87867f8-0a8c-48d8-b6ef-234caa33e41f" />
  <br>
  <em>Settings UI</em>
</p>

### Volume Mapping

To ensure data persistence, make sure you map the `/config` directory to a persistent volume on your host system:

```bash
-v /your-path/appdata/huntarr:/config
```

---

## The Perfect Pair: Huntarr & Cleanuperr

<p align="center">
  <img src="https://github.com/plexguide/Huntarr.io/blob/main/frontend/static/logo/128.png?raw=true" alt="Huntarr" width="64" height="64">
  <span style="font-size: 32px; margin: 0 15px;">+</span>
  <img src="https://github.com/flmorg/cleanuperr/blob/main/Logo/128.png?raw=true" alt="Cleanuperr" width="64" height="64">
</p>

**Huntarr** is the compulsive librarian who finds missing media and upgrades your existing content. It fills in the blanks and improves what you already have.

**Cleanuperr** ([![GitHub stars](https://img.shields.io/github/stars/flmorg/cleanuperr?style=social)](https://github.com/flmorg/cleanuperr/stargazers)) is the janitor of your server; it keeps your download queue spotless, removes clutter, and blocks malicious files.

When combined, these tools create a powerful, self-sufficient media automation stack:

- **Huntarr** hunts for content to add to your library
- **Cleanuperr** ensures only clean downloads get through
- Together, they create a reliable, hands-off media management system

Learn more about **Cleanuperr** at [https://github.com/flmorg/cleanuperr](https://github.com/flmorg/cleanuperr)

## Tips

- **First-Time Setup**: Navigate to the web interface after installation to create your admin account with 2FA option
- **API Connections**: Configure connections to your *Arr applications through the dedicated settings pages
- **Search Frequency**: Adjust Sleep Duration (default: 900 seconds) based on your indexer's rate limits
- **Batch Processing**: Set Hunt Missing and Upgrade values to control how many items are processed per cycle
- **Queue Management**: Use Minimum Download Queue Size to pause searching when downloads are backed up
- **Skip Processing**: Enable Skip Series/Movie/Artist Refresh to significantly reduce disk I/O and database load
- **Future Content**: Keep Skip Future Items enabled to avoid searching for unreleased content
- **Authentication**: Enable two-factor authentication for additional security on your Huntarr instance
- **API Rate Limits**: Configure hourly API caps to prevent rate limiting by your indexers
- **Universal Timeouts**: All apps use consistent 120s timeouts for reliable command completion
- **Monitored Only**: Filter searches to focus only on content you've marked as monitored
- **Notifications**: Configure Apprise notifications to get alerts when media is processed

## Troubleshooting

- **API Connection Issues**: Verify your API key and URL in the Settings page (check for missing http:// or https://)
- **Config URLs**: It is best practice to omit the trailing slash (/) at the end of the URL for each service. For Sonarr, use http://10.10.10.1:8989 instead of http://10.10.10.1:8989/
- **Authentication Problems**: If you forget your password, delete `/config/user/credentials.json` and restart
- **Two-Factor Authentication**: If locked out of 2FA, remove credentials file to reset your account
- **Web Interface Not Loading**: Confirm port 9705 is correctly mapped and not blocked by firewalls
- **Logs Not Showing**: Check permissions on the `/config/logs/` directory inside your container
- **Missing State Data**: State files in `/config/stateful/` track processed items; verify permissions
- **Docker Volume Issues**: Ensure your volume mount for `/config` has correct permissions and ownership
- **Command Timeouts**: Default values are now command_wait_delay=1s and command_wait_attempts=600
- **Debug Information**: Enable Debug Mode temporarily to see detailed API responses in the logs
- **API Timeout Errors**: All apps now use universal timeout settings (120s) from general.json
- **Consistent Log Filtering**: If app-specific logs show mixed content, reduce historical data from 5KB to 1KB
- **Swaparr Issues**: Ensure proper handling of non-dictionary records in queue data
- **App-Specific Problems**: Check GitHub Issues for known problems and solutions

## Change Log
Visit: https://github.com/plexguide/Huntarr.io/releases/
