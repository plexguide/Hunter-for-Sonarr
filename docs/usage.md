# Usage Guide

This guide covers the day-to-day usage of Huntarr, including monitoring media hunting, interpreting logs, and managing your hunt cycles.

## Dashboard Overview

The Huntarr dashboard provides a quick overview of your media hunting status:

![Dashboard Example](assets/img/dashboard-example.png)

Key elements include:

- **Connection Status**: Shows which media applications are connected
- **Live Hunts Executed**: Statistics on searches and upgrades triggered for each application
- **API Usage**: Real-time monitoring of API request rates to prevent rate limiting

## Media Hunting Status

### Starting and Stopping Hunts

To manually control the hunting process:

1. From the home screen, use the control buttons in the app cards
2. Click **Reset Cycle** to restart the hunting cycle for a specific application
3. The hunts will automatically run based on your configured schedule

### Monitoring Progress

The statistics cards on the home page provide real-time information:

- **Searches Triggered**: Count of missing media searches initiated
- **Upgrades Triggered**: Count of quality upgrade searches initiated

These counters reset automatically based on your stateful management settings or when you manually reset them using the **Reset** button in the Statistics card header.

## Logs

The Logs section provides detailed information about Huntarr's activities:

1. Navigate to the **Logs** section from the sidebar
2. Use the dropdown to select which application's logs to view

### Log Filtering

To filter logs:

1. Use the search box at the top of the logs view
2. Enter keywords to find specific events (e.g., "search", "upgrade", "error")
3. Click **Clear** to reset the filter

### Log Levels

Logs are color-coded by severity:

- <span style="color:#e74c3c">**ERROR**</span>: Critical issues that need attention
- <span style="color:#f39c12">**WARNING**</span>: Potential issues that might need attention
- <span style="color:#3498db">**INFO**</span>: General information about normal operations
- <span style="color:#7f8c8d">**DEBUG**</span>: Detailed information for troubleshooting (only visible with Debug Mode enabled)

### Common Log Messages

#### Normal Operation Messages

- `Processing missing items for [app]`: Huntarr is searching for missing media
- `Processing upgradable items for [app]`: Huntarr is searching for quality upgrades
- `Searching for [media item]`: A specific item is being searched
- `Command sent to [app], waiting for completion`: A search command was initiated
- `Search completed successfully for [media item]`: Item was successfully searched
- `Sleep cycle started`: Huntarr is in sleep mode between processing cycles

#### Warning Messages

- `API rate limit approaching for [app]`: API requests are getting close to the configured limit
- `Maximum download queue size reached`: Downloads are paused due to queue size limit
- `Item is not monitored, skipping`: An item was skipped because it isn't monitored
- `Item has future release date, skipping`: Item skipped due to future release date

#### Error Messages

- `API connection error for [app]`: Connection to the media app failed
- `API key invalid for [app]`: API key authentication failed
- `Command timeout`: A search command took too long to complete
- `Failed to process [media item]`: Processing of a specific item failed

## History

The History section shows a record of all processed media:

1. Navigate to the **History** section from the sidebar
2. Use the dropdown to filter by application
3. Use the search box to find specific media items

History entries include:

- Media name
- Action taken (search or upgrade)
- Result (found, not found, error)
- Date and time processed

## Scheduling

The Scheduling section allows you to visually manage when hunting occurs:

1. Navigate to the **Scheduling** section
2. Click on time slots in the calendar to toggle activity
3. Use the controls to:
   - Add specific schedule rules
   - Copy schedules between days
   - Clear schedules

## Managing Apps

### Resetting App Cycles

If you want to restart the hunting process for a specific app:

1. From the home screen, locate the app card
2. Click the **Reset Cycle** button
3. The app will restart its hunting cycle from the beginning

### Viewing API Usage

To monitor API usage and avoid rate limiting:

1. Check the API counts in each app card on the dashboard
2. The format shows: `API: [current count] / [limit]`
3. The color indicates status:
   - Green: Safe usage level
   - Yellow: Approaching limit
   - Red: At or near limit

## Stateful Management

Huntarr uses stateful management to track which media items have been processed:

- **Initial State Created**: When the state was first created
- **State Reset Date**: When the state will automatically reset

To manually reset the state:

1. Go to **Settings > General > Stateful Management**
2. Click the **Emergency Reset** button
3. Confirm to clear all processed media IDs

## Managing Settings

### When to Adjust Settings

Consider adjusting your settings when:

1. You see frequent API rate limit warnings
2. Media searches are too aggressive or not aggressive enough
3. Your download queue is consistently full
4. You need to prioritize certain media types

### Recommended Workflow

For an optimal Huntarr experience:

1. Start with conservative settings (low search counts, high sleep durations)
2. Monitor logs and API usage for a few days
3. Gradually increase search intensity if your system and APIs can handle it
4. Use scheduling to run more intensive searches during off-peak hours

## Practical Examples

### Scenario: Initial Library Population

When first setting up Huntarr with a large backlog of missing media:

1. Set higher values for **Missing Items to Search**
2. Set **Upgrade Items to Search** to 0 temporarily
3. Use scheduling to run 24/7 until the initial backlog is cleared
4. Monitor API usage closely to avoid hitting limits

### Scenario: Maintenance Mode

For ongoing maintenance once your library is well-populated:

1. Reduce **Missing Items to Search** to lower values
2. Increase **Upgrade Items to Search** to improve quality over time
3. Set longer **Sleep Duration** values
4. Schedule intensive searches for overnight hours only

## Next Steps

Now that you understand how to use Huntarr, check out the [FAQ](faq.md) for answers to common questions and advanced usage tips. 