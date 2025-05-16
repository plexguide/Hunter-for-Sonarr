---
sidebar_position: 3
---

# Configuration Guide

After installing Huntarr, you'll need to configure it to connect with your *arr applications and set up its hunting behavior. This guide will walk you through the process.

## Initial Setup

1. Access the Huntarr web interface at `http://YOUR_SERVER_IP:9705`
2. Create your administrator account
3. Optionally enable two-factor authentication for additional security

## Connecting *Arr Applications

Huntarr needs to connect to your media management applications to find missing content and quality upgrades.

### Adding a Sonarr Connection

1. Navigate to the **Settings** page
2. Select the **Sonarr** tab
3. Click **Add New Connection**
4. Configure the following fields:
   - **Name**: A descriptive name (e.g., "Sonarr Main")
   - **URL**: The full URL including port (e.g., `http://10.10.10.1:8989`)
   - **API Key**: Your Sonarr API key (found in Settings > General in Sonarr)
   - **Base Path**: Leave blank unless your Sonarr instance uses a custom base path
5. Click **Test Connection** to verify settings
6. Click **Save** when successful

### Adding Radarr/Lidarr/Readarr/Whisparr

Follow the same steps as above, selecting the appropriate tab for each application. Each *arr application requires:

- A valid URL (without trailing slash)
- A valid API key
- Proper base path if used

## General Settings

Configure global behavior in the **General** tab:

### Hunt Settings

- **Hunt Missing**: Number of missing items to search for per run (default: 10)
- **Hunt Upgrades**: Number of upgrades to search for per run (default: 10)
- **Sleep Duration**: Seconds to wait between cycles (default: 900)
- **Minimum Download Queue Size**: Pause hunting when download queue exceeds this value (default: 5)

### API Management

- **API Hourly Cap**: Maximum API calls per hour (default: 100)
- **Universal API Timeout**: Seconds to wait for API responses (default: 120)
- **Skip Series/Movie Refresh**: Enable to reduce disk I/O (recommended)
- **Skip Future Items**: Enable to avoid searching for unreleased content (recommended)

## Advanced Configuration

### Debug Mode

Enable Debug Mode temporarily to troubleshoot connection issues by showing detailed API responses in logs.

### Command Timing

- **Command Wait Delay**: Seconds to wait between command status checks (default: 1)
- **Command Wait Attempts**: Maximum number of attempts to check command status (default: 600)

## Configuration Tips

- **URLs**: Omit trailing slashes from URLs (use `http://10.10.10.1:8989` not `http://10.10.10.1:8989/`)
- **API Keys**: Double-check API keys if connection tests fail
- **Network Access**: Ensure Huntarr can reach your *arr applications via the network
- **Rate Limits**: Adjust API hourly caps based on your indexer's rate limits
- **Monitored Only**: By default, Huntarr only processes content you've marked as monitored

## Troubleshooting

If you encounter configuration issues:

- Check API keys and URLs carefully
- Verify network connectivity between Huntarr and your *arr applications
- Review logs for specific error messages
- Temporarily enable Debug Mode for more detailed logging
- Ensure proper permissions for the `/config` directory 