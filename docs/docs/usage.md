---
sidebar_position: 4
---

# Usage Guide

Once you've installed and configured Huntarr, it will automatically begin its hunt and upgrade process. This guide explains how to monitor and use Huntarr on a daily basis.

## The Huntarr Dashboard

The Huntarr homepage provides real-time statistics and status information:

- **Hunt Statistics**: Shows the number of missing media items found and upgrade searches performed
- **Application Status**: Displays connection status for each configured *arr application
- **API Usage**: Visual indicators show API usage for each application relative to your configured limits
- **Recent Activity**: Lists the most recent hunt operations and their results

## Monitoring Hunts

### Live Logs

The **Logs** tab provides real-time insight into Huntarr's operations:

1. Navigate to the **Logs** tab in the web interface
2. Use the filter options to focus on specific applications or log levels
3. Watch as Huntarr searches for missing content and quality upgrades
4. Click the **Refresh** button to update logs manually if auto-refresh is disabled

### Understanding Hunt Cycles

Huntarr operates in continuous cycles:

1. **Connect**: Huntarr connects to each configured *arr application
2. **Missing Hunt**: Searches for missing content based on your "Hunt Missing" setting
3. **Upgrade Hunt**: Searches for content below quality cutoff based on your "Hunt Upgrades" setting
4. **Sleep**: Waits for the configured sleep duration before starting the next cycle

Each hunt cycle is independent, so if one application has issues, others will still be processed.

## Manual Controls

While Huntarr is designed to run autonomously, you can control aspects of its operation:

### Pausing and Resuming

To temporarily pause Huntarr:

1. Navigate to the **Settings** page
2. Toggle the **Pause Hunting** switch to ON
3. Huntarr will complete its current cycle and then pause
4. Toggle the switch back to OFF to resume operations

### Forcing a Hunt

To initiate an immediate hunt (bypassing the sleep timer):

1. Navigate to the **Dashboard**
2. Click the **Force Hunt** button
3. Huntarr will start a new hunt cycle immediately

## Working with Results

Huntarr does not modify your media library directly - it works through your existing *arr applications:

- Missing content will be added to your *arr application's download queue
- Upgrades will be initiated according to your *arr application's quality settings
- All actions will be visible in both Huntarr's logs and your *arr application's history

## Daily Operation Tips

For the best experience with Huntarr:

- **Check the dashboard daily** for a quick overview of hunt statistics
- **Review logs periodically** to identify any recurring issues
- **Adjust hunt settings** if you find download queues getting too large
- **Increase sleep duration** if you notice indexers rate-limiting your searches
- **Decrease API hourly caps** if your indexers have strict rate limits

## Monitoring Download Progress

Since Huntarr initiates downloads through your *arr applications, you should:

1. Check your *arr applications' download queues to monitor progress
2. Use your download client to view active downloads
3. Verify that media is being added to your library correctly

## Maintaining Huntarr

To keep Huntarr running smoothly:

- **Update regularly** when new versions are released
- **Back up the configuration directory** before major updates
- **Check logs periodically** for any errors or warnings
- **Adjust settings** as your library size and needs change

## Understanding API Rate Management

Huntarr includes sophisticated API rate management:

- The dashboard shows current API usage for each application
- If usage approaches your configured hourly cap, Huntarr will intelligently slow down requests
- When the cap is reached, Huntarr will pause that application's hunting until the next hour
- Other applications will continue to be processed normally 