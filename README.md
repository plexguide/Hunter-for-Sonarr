<h2 align="center">Huntarr - Find Missing & Upgrade Media Items</h2> 

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

## Table of Contents
- [Overview](#overview)
- [Related Projects](#related-projects)
- [Features](#features)
- [How It Works](#how-it-works)
- [Configuration Options](#configuration-options)
- [Persistent Storage](#persistent-storage)
- [Installation Methods](#installation-methods)
  - [Docker Run](#docker-run)
  - [Docker Compose](#docker-compose)
  - [Unraid Users](#unraid-users)
- [Use Cases](#use-cases)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Overview

Huntarr-Sonarr continuously searches your Sonarr library for:
1. Shows with missing episodes
2. Episodes that need quality upgrades

It automatically triggers searches while being gentle on your indexers, helping you complete your collection with the best available quality.

## Related Projects

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
- 🔁 **State Tracking**: Remembers which items have been processed to avoid duplicate searches
- ⚙️ **Configurable Reset Timer**: Automatically resets search history after a configurable period
- 📦 **Modular Design**: Modern codebase with separated concerns for easier maintenance
- 🔮 **Future Item Skipping**: Skip processing items with future release dates
- 💾 **Reduced Disk Activity**: Option to skip metadata refresh before processing
- 📝 **Stateful Operation**: Processed state is now permanently saved between restarts
- ⚙️ **Advanced Settings**: Control API timeout, command wait parameters, and more

## Indexers Approving of Huntarr:
* https://ninjacentral.co.za

## How It Works

1. **Initialization**: Connects to your Sonarr instance and analyzes your library
2. **Missing Content**: 
   - Identifies items with missing episodes
   - Randomly or sequentially selects items to process (configurable)
   - Refreshes metadata (optional) and triggers searches
   - Skips items with future release dates (configurable)
3. **Quality Upgrades**:
   - Finds items that don't meet your quality cutoff settings
   - Processes them in configurable batches
   - Uses smart pagination to handle large libraries
   - Can operate in random or sequential mode (configurable)
   - Skips items with future release dates (configurable)
4. **State Management**:
   - Tracks which items have been processed
   - Stores this information persistently in the `/config` volume
   - Automatically resets this tracking after a configurable time period
5. **Repeat Cycle**: Waits for a configurable period before starting the next cycle

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| API_KEY | (Required) | Your Sonarr API key |
| API_URL | http://localhost:8989 | URL to your Sonarr instance |
| API_TIMEOUT | 60 | Timeout for API requests in seconds |
| MONITORED_ONLY | true | Only process monitored shows and episodes |
| HUNT_MISSING_SHOWS | 1 | Maximum number of missing shows to process per cycle |
| HUNT_UPGRADE_EPISODES | 0 | Maximum number of episodes to upgrade per cycle |
| SLEEP_SECONDS | 1800 | Time to wait between cycles (in seconds) |
| STATE_RESET_HOURS | 168 | Hours after which processed items will be forgotten (0 to disable) |
| RANDOM_MISSING | true | Select missing shows randomly instead of sequentially |
| RANDOM_UPGRADES | true | Select upgrade episodes randomly instead of sequentially |
| SKIP_FUTURE_EPISODES | true | Skip processing episodes with future air dates |
| SKIP_SERIES_REFRESH | true | Skip refreshing series metadata before processing |
| COMMAND_WAIT_SECONDS | 1 | Time to wait between commands (in seconds) |
| COMMAND_WAIT_ATTEMPTS | 600 | Maximum number of attempts for commands |
| MINIMUM_DOWNLOAD_QUEUE_SIZE | -1 | Skip processing if queue is larger than this (use -1 to disable) |
| LOG_EPISODE_ERRORS | false | Log individual episode errors |
| DEBUG_API_CALLS | false | Log detailed API call information |

### Viewing Logs

To view the logs, simply run:

```bash
docker logs huntarr-sonarr
```

### Running Manually

If you want to run Huntarr-Sonarr manually, you can enter the container and run:

```bash
huntarr-sonarr
```

This will start the process with output directly to the console.

## Persistent Storage

Huntarr stores all its configuration and state information in persistent storage, ensuring your settings and processed state are maintained across container restarts and updates.

### Storage Locations

The following directories are used for persistent storage:

- `/config/stateful/` - Contains the state tracking files for processed items

### Data Persistence

All data in these directories is maintained across container restarts. This means:

1. The list of items that have already been processed will be maintained
2. After a container update or restart, Huntarr will continue from where it left off

### Volume Mapping

To ensure data persistence, make sure you map the `/config` directory to a persistent volume on your host system:

```bash
-v /path/to/config:/config
```

This mapping is included in all of the installation examples above.

## Installation Methods

### Docker Run

```bash
docker run -d --name huntarr-sonarr \
  --restart always \
  -v /path/to/config:/config \
  -e API_KEY=your-sonarr-api-key \
  -e API_URL=http://sonarr:8989 \
  -e MONITORED_ONLY=true \
  -e HUNT_MISSING_SHOWS=1 \
  -e HUNT_UPGRADE_EPISODES=0 \
  -e SLEEP_SECONDS=1800 \
  -e STATE_RESET_HOURS=168 \
  -e RANDOM_MISSING=true \
  -e RANDOM_UPGRADES=true \
  -e SKIP_FUTURE_EPISODES=true \
  -e SKIP_SERIES_REFRESH=true \
  -e COMMAND_WAIT_SECONDS=1 \
  -e COMMAND_WAIT_ATTEMPTS=600 \
  -e MINIMUM_DOWNLOAD_QUEUE_SIZE=-1 \
  -e LOG_EPISODE_ERRORS=false \
  -e DEBUG_API_CALLS=false \
  huntarr/4sonarr:latest
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: "3.8"
services:
  huntarr-sonarr:
    image: huntarr/4sonarr:latest
    container_name: huntarr-sonarr
    restart: unless-stopped
    volumes:
      - /path/to/config:/config
    environment:
      - API_KEY=your-sonarr-api-key
      - API_URL=http://sonarr:8989
      - API_TIMEOUT=60
      - MONITORED_ONLY=true
      - HUNT_MISSING_SHOWS=1
      - HUNT_UPGRADE_EPISODES=0
      - SLEEP_SECONDS=1800
      - STATE_RESET_HOURS=168
      - RANDOM_MISSING=true
      - RANDOM_UPGRADES=true
      - SKIP_FUTURE_EPISODES=true
      - SKIP_SERIES_REFRESH=true
      - COMMAND_WAIT_SECONDS=1
      - COMMAND_WAIT_ATTEMPTS=600
      - MINIMUM_DOWNLOAD_QUEUE_SIZE=-1
      - LOG_EPISODE_ERRORS=false
      - DEBUG_API_CALLS=false
```

Then run:

```bash
docker-compose up -d
```

### Unraid Users

For Unraid users, you can install Huntarr-Sonarr using the Community Applications plugin:

1. Open the Unraid web interface and navigate to the **Apps** tab
2. Search for "Huntarr" or "Huntarr-Sonarr" in the search box
3. Click on the Huntarr-Sonarr app
4. Fill in the following settings:
   - **Container Name**: huntarr-sonarr
   - **Host Path 1**: Choose a path for persistent storage, e.g., `/mnt/user/appdata/huntarr-sonarr`
   - Set your environment variables:
     - API_KEY: your-sonarr-api-key
     - API_URL: http://tower:8989 (replace "tower" with your Sonarr container name or IP)
     - Other variables as desired
5. Click **Apply** to create the container

Alternatively, you can add the container manually via the **Docker** tab:

1. Click **Add Container** in the Docker tab
2. Enter the following details:
   - **Name**: huntarr-sonarr
   - **Repository**: huntarr/4sonarr:latest
   - Add a path mapping: `/config` to `/mnt/user/appdata/huntarr-sonarr`
   - Add the environment variables as listed above
3. Click **Apply** to create the container

## Use Cases

- **Library Completion**: Gradually fill in missing content in your media library
- **Quality Improvement**: Automatically upgrade item quality as better versions become available
- **New Item Setup**: Automatically find media for newly added items
- **Background Service**: Run it in the background to continuously maintain your library
- **Smart Rotation**: With state tracking, ensures all content gets attention over time
- **Disk Usage Optimization**: Skip refreshing metadata to reduce disk wear and tear
- **Efficient Searching**: Skip processing items with future release dates to save resources
- **Stateful Operation**: Maintain processing state across container restarts and updates

## Tips

- **API Connection**: Make sure your API_KEY and API_URL are correct
- **Adjusting Speed**: Lower the SLEEP_SECONDS to search more frequently (be careful with indexer limits)
- **Batch Size Control**: Adjust HUNT_MISSING_SHOWS and HUNT_UPGRADE_EPISODES values based on your indexer's rate limits
- **Monitored Status**: Set MONITORED_ONLY to false if you want to download all missing content regardless of monitored status
- **System Resources**: The application uses minimal resources and can run continuously on even low-powered systems
- **Hard Drive Saving**: Enable SKIP_SERIES_REFRESH to reduce disk activity
- **Search Efficiency**: Keep SKIP_FUTURE_EPISODES enabled to avoid searching for unavailable content
- **Persistent Storage**: Make sure to map the `/config` volume to preserve state information
- **Random vs Sequential**: Configure RANDOM_MISSING and RANDOM_UPGRADES based on your preference for processing style

## Troubleshooting

- **API Key Issues**: Check that your API_KEY is correct
- **Connection Problems**: Ensure the API_URL is accessible from where you're running the application
- **Logs**: Check the container logs with `docker logs huntarr-sonarr`
- **Settings Not Persisting**: Verify your volume mount for `/config` is configured correctly
- **State Files**: The application stores state in `/config/stateful/` - if something seems stuck, you can try deleting these files
- **Excessive Disk Activity**: If you notice high disk usage, try enabling SKIP_SERIES_REFRESH

---

This application helps automate the tedious process of finding missing content and quality upgrades in your media collection, running quietly in the background while respecting your indexers' rate limits.

---

Thanks to: 

* [IntensiveCareCub](https://www.reddit.com/user/IntensiveCareCub/) for the Hunter to Huntarr idea!
* [ZPatten](https://github.com/zpatten) for adding the Queue Size and Delay Commands!
