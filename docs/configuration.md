# Configuration Guide

This guide will help you configure Huntarr to work with your media applications and set up optimal media hunting parameters.

## Initial Setup

After installation, access the Huntarr web interface at `http://your-ip:8123` and follow these steps:

1. **Create an admin account** on the first launch
2. **Log in** to access the dashboard
3. **Configure your *arr applications** in the Settings section

## Connecting Media Applications

Huntarr works with the following media applications:

- Sonarr (TV shows)
- Radarr (Movies)
- Lidarr (Music)
- Readarr (Books)
- Whisparr (Adult content)

### Adding an Application Instance

1. Go to **Settings** and select the appropriate tab (Sonarr, Radarr, etc.)
2. Fill in the following details:
   - **Name**: A friendly name for this instance
   - **URL**: The full URL to your instance (e.g., `http://192.168.1.100:8989`)
   - **API Key**: Your instance's API key (found in Settings > General in your *arr application)
   - **Enabled**: Toggle to enable/disable this instance

![Settings Configuration Example](assets/img/settings-example.png)

### Multi-Instance Support

Huntarr supports multiple instances of each application. For example, you can have:

- Sonarr for TV shows and another for anime
- Radarr for movies and another for documentaries

To add additional instances, click the **Add Instance** button in the respective application's settings tab.

## Hunting Configuration

### Global Hunting Options {#global-hunting-options}

Under the **General** tab in Settings, you can configure:

- **Debug Mode** {#debug-mode}: Enable for verbose logging
- **Display Resources**: Show/hide the Resources section on the home page
- **API Timeout**: Timeout for API requests in seconds
- **Maximum Download Queue Size**: Limit downloads to prevent overwhelming your system

### Application-Specific Options

Each media app has its own configuration options:

#### Sonarr Options

- **Missing Search Mode**: 
  - Episodes: Search for individual episodes
  - Seasons/Packs: Search for entire seasons at once
  - Shows: Search for entire shows
- **Upgrade Mode**: Set how upgrades are searched
- **Missing Items to Search**: Number of missing items to search per cycle
- **Upgrade Items to Search**: Number of upgrades to search per cycle
- **Sleep Duration**: Time between processing cycles
- **API Cap - Hourly**: Maximum API requests per hour
- **Monitored Only**: Only search for monitored items
- **Skip Future Episodes**: Skip searching for episodes with future air dates

#### Radarr Options

- **Missing Movies to Search**: Number of missing movies to search per cycle
- **Movies to Upgrade**: Number of movies to upgrade per cycle
- **API Cap - Hourly**: Maximum API requests per hour
- **Skip Future Releases**: Skip searching for movies not yet released
- **Release Type for Future Status**: Which release type to use for determining if a movie is released

Similar options are available for Lidarr, Readarr, and Whisparr, tailored to the specific media types.

## Stateful Management {#stateful-management}

Huntarr maintains a record of processed media to avoid re-searching for the same items repeatedly.

- **State Reset Interval**: Controls how long Huntarr remembers processed media
- **Emergency Reset**: Button to clear all processed items if you want to start fresh

To customize this:

1. Go to **Settings > General > Stateful Management**
2. Adjust the **State Reset Interval** (in hours)
3. Monitor the **State Reset Date** to know when your state will be cleared

## Scheduling

Huntarr includes a scheduling feature that lets you control when media hunting occurs.

1. Navigate to the **Scheduling** section
2. Use the calendar interface to set active and inactive periods
3. Create rules for specific days or time ranges

Example schedules:

- Run only during overnight hours (1 AM - 6 AM)
- Disable on weekends
- Run at reduced capacity during peak Internet usage times

## Advanced Features {#advanced-features}

### Swaparr Integration

Huntarr includes Swaparr integration to manage stalled downloads:

1. Go to **Settings > Swaparr**
2. Enable Swaparr and configure:
   - **Maximum Strikes**: Number of strikes before removing a stalled download
   - **Max Download Time**: How long a download can stall before getting a strike
   - **Ignore Above Size**: Skip large files that might take longer to download
   - **Dry Run Mode**: Test without actually removing downloads

### Security Settings {#security-settings}

To secure your Huntarr instance:

1. Go to **Settings > General > Security**
2. Configure **Local Network Auth Bypass** to allow access without login when connecting from local IPs
3. Toggle **SSL Verification** for your API connections

## Saving Your Configuration

After making changes to any settings page, be sure to:

1. Click the **Save** button at the bottom of the page
2. Wait for the "Settings saved successfully" confirmation message

## Testing Your Configuration

After configuring each application:

1. Click the **Test Connection** button next to each instance
2. Verify that the status shows "Connected"
3. Check your home page to see all connected instances

## Troubleshooting

### Connection Issues

If you see "Not Connected" status:

- Verify the URL is correct and includes http:// or https://
- Ensure the API key is correct
- Check that the application is running and accessible from Huntarr
- Verify any firewall settings that might block connections

### API Rate Limiting

If you notice API rate limit warnings:

- Reduce the hourly cap for affected applications
- Increase the sleep duration between cycles
- Prioritize applications based on importance

### Performance Tuning

For optimal performance:

- Adjust the number of items to search based on your system capabilities
- Use longer sleep durations for less critical media types
- Consider running Huntarr on the same machine as your *arr applications to reduce network latency

## Next Steps

Once you've configured your applications, check out the [Usage Guide](usage.md) to learn how to monitor Huntarr's progress and interpret its logs. 