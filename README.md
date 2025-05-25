<h2 align="center">Huntarr - Find Missing & Upgrade Media Items</h2> 

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr Logo" width="100" height="100">
</p>

---

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2> 

<img src="https://github.com/user-attachments/assets/1ea6ca9c-0909-4b6a-b573-f778b65af8b2" width="100%"/>

#### ⭐ Show Your Support for Open Source!

If Huntarr has been helpful to you and you appreciate the power of open-source software, please consider giving this repository a star. Your gesture will greatly support our efforts and help others discover Huntarr!

<a href="https://github.com/plexguide/Huntarr.io/stargazers">
  <img src="https://reporoster.com/stars/plexguide/Huntarr.io" alt="Stargazers repo roster for @plexguide/Huntarr.io" />
</a>
 
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
- [Why You Need Huntarr](#why-you-need-huntarr)
- [Other Projects](#other-projects)
- [Community](#community)
- [Indexers Approving of Huntarr](#indexers-approving-of-huntarr)
- [Installation Methods](#installation-methods)
- [How It Works](#how-it-works)
- [Web Interface](#web-interface)
  - [How to Access](#how-to-access)
  - [Web UI Settings](#web-ui-settings)
  - [Volume Mapping](#volume-mapping)
- [Change Log](#change-log)

## Overview

This application continually searches your media libraries for missing content and items that need quality upgrades. It automatically triggers searches for both missing items and those below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your media collection with the best available quality.

For detailed documentation, please visit our <a href="https://plexguide.github.io/Huntarr.io/" target="_blank" rel="noopener noreferrer">Wiki</a>.

## Why You Need Huntarr

Think of it this way: Sonarr/Radarr are like having a mailman who only delivers new mail as it arrives, but never goes back to get mail that was missed or wasn't available when they first checked. Huntarr is like having someone systematically go through your entire wishlist and actually hunt down all the missing pieces.

Here's the key thing most people don't understand: Your *arr apps only monitor RSS feeds for NEW releases. They don't go back and search for the missing episodes/movies already in your library. This means if you have shows you added after they finished airing, episodes that failed to download initially, or content that wasn't available on your indexers when you first added it, your *arr apps will just ignore them forever.

Huntarr solves this by continuously scanning your entire library, finding all the missing content, and systematically searching for it in small batches that won't overwhelm your indexers or get you banned. It's the difference between having a "mostly complete" library and actually having everything you want.

Most people don't even realize they have missing content because their *arr setup "looks" like it's working perfectly - it's grabbing new releases just fine. But Huntarr will show you exactly how much you're actually missing, and then go get it all for you automatically.

Without Huntarr, you're basically running incomplete automation. You're only getting new stuff as it releases, but missing out on completing existing series, filling gaps in movie collections, and getting quality upgrades when they become available. It's the tool that actually completes your media automation setup.

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

- 🐋 **[Docker Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html)**
- 🪟 **[Windows Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#windows-installation)**
- 🍏 **[macOS Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#macos-installation)**
- 🔵 **[Unraid Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#unraid-installation)**
- 🔧 **[Alternative Methods](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#alternative-methods)**

Special thanks to [Nwithan8](https://github.com/nwithan8) for maintaining the Unraid templates and helping Huntarr grow through the Unraid Community Applications repository.

## How It Works

### 🔄 Continuous Automation Cycle

<i class="fas fa-1"></i> **Connect & Analyze** - Huntarr connects to your Sonarr/Radarr/Lidarr/Readarr/Whisparr/Eros instances and analyzes your media libraries to identify both missing content and potential quality upgrades.

<i class="fas fa-2"></i> **Hunt Missing Content** - Efficiently refreshes by skipping metadata to reduce disk I/O and database load, automatically skips content with future release dates, provides precise control over how many items to process per cycle, and focuses only on content you've marked as monitored.

<i class="fas fa-3"></i> **Hunt Quality Upgrades** - Finds content below your quality cutoff settings for improvement, uses batch processing to set specific numbers of upgrades per cycle, automatically pauses when download queue exceeds your threshold, and waits for commands to complete with consistent timeouts.

<i class="fas fa-4"></i> **API Management** - Implements hourly caps to prevent overloading your indexers, uses consistent API timeouts (120s) across all applications, identifies as Huntarr to all Arr applications with consistent headers, and provides visual indicators showing API usage limits.

<i class="fas fa-5"></i> **Repeat & Rest** - Huntarr waits for your configured interval (adjustable in settings) before starting the next cycle, ensuring your indexers aren't overloaded while maintaining continuous improvement of your library.

## Web Interface

Huntarr's live homepage will provide you statics about how many hunts have been pursed regarding missing media and upgrade searches! Note: Numbers reflected are but all required for testing. 

<p align="center">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/c060962c-01ee-4f53-a5ee-c67f31432e40" />
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

## Change Log
Visit: https://github.com/plexguide/Huntarr.io/releases/
