# Swaparr Integration Guide

> Manage stalled and stuck downloads automatically using Huntarr's integration with Swaparr

## What is Swaparr?

Swaparr is a complementary tool integrated into Huntarr that addresses a common issue in media automation: stalled downloads. Specifically designed for torrent users, Swaparr:

- Identifies downloads that have stopped progressing
- Applies a "strikes" system to monitor problematic downloads
- Automatically removes stalled downloads after defined thresholds
- Helps maintain a clean, efficient download queue

Originally a standalone project, Swaparr has been fully integrated into Huntarr to provide a seamless experience for managing problematic downloads.

## Why Swaparr is Valuable

Without Swaparr, stalled downloads can:

- Consume slots in your download client
- Prevent new downloads from starting
- Require manual intervention to clear
- Lead to media items remaining in a perpetual "searching" state

Swaparr solves these problems by automatically monitoring and managing these problematic downloads, ensuring your download queue remains healthy and active.

## How Swaparr Works

Swaparr follows a systematic approach to managing stalled downloads:

1. **Detection**: Identifies downloads that haven't progressed for a specified period
2. **Strike System**: Assigns "strikes" to downloads that consistently fail to progress
3. **Removal**: Removes downloads that reach the maximum strike count
4. **Reporting**: Logs all actions for your review

### The Strike System Explained

The strike system works as follows:

1. A download is detected as stalled when it meets these criteria:
   - Has been downloading longer than the defined maximum download time
   - Has made no progress during the checking period
   - Is below the "ignore above size" threshold

2. When a stalled download is identified:
   - It receives a strike
   - It remains in the download queue
   - Its strike count is stored in Huntarr's database

3. During subsequent checks:
   - If the download has resumed progress, strikes are maintained (not increased)
   - If the download remains stalled, it receives another strike
   - If strikes reach the maximum limit, the download is removed

## Configuring Swaparr in Huntarr

### Accessing Swaparr Settings

1. Go to **Settings**
2. Select the **Swaparr** tab
3. Enable or disable the Swaparr integration using the toggle

### Available Settings

| Setting | Description | Recommended Value |
|---------|-------------|-------------------|
| **Enable Swaparr** | Turn Swaparr functionality on/off | Enabled |
| **Maximum Strikes** | Number of strikes before removing a download | 3-5 |
| **Max Download Time** | How long a download can be active before being eligible for strikes | 2h-12h |
| **Ignore Above Size** | Skip large files that might legitimately take longer | 25GB |
| **Remove From Client** | Whether to remove the download from the torrent/usenet client | Enabled |
| **Dry Run Mode** | Log actions but don't actually remove downloads | Enable initially |

### Setting Up For the First Time

When setting up Swaparr for the first time, we recommend:

1. Enable **Dry Run Mode** initially
2. Set **Maximum Strikes** to 3
3. Set **Max Download Time** to a reasonable value based on your connection (e.g., 2h)
4. Monitor the logs for a few days to see what would be removed
5. Once comfortable with the identified stalled downloads, disable Dry Run Mode

## Advanced Swaparr Configuration

### Download Client Considerations

Swaparr works with various download clients through your *arr applications:

- **qBittorrent**: Fully compatible
- **Transmission**: Fully compatible
- **Deluge**: Fully compatible
- **rTorrent**: Fully compatible
- **SABnzbd**: Compatible for usenet downloads
- **NZBGet**: Compatible for usenet downloads

### Size Thresholds

The **Ignore Above Size** setting is particularly important:

- **Smaller value** (e.g., 5GB): More aggressive management, might remove large legitimate downloads
- **Medium value** (e.g., 25GB): Good balance for most users
- **Larger value** (e.g., 100GB): Only the largest downloads will be ignored
- **Extreme value** (e.g., 1TB): Effectively disables the size filter

### Client-Specific Recommendations

Depending on your download client, consider these adjustments:

**qBittorrent**:
```yaml
swaparr:
  max_strikes: 3
  max_download_time: 2h
  ignore_above_size: 25GB
```

**Transmission** (tends to handle stalled torrents differently):
```yaml
swaparr:
  max_strikes: 4
  max_download_time: 3h
  ignore_above_size: 30GB
```

## Monitoring and Maintenance

### Viewing Swaparr Status

To monitor Swaparr's activity:

1. Go to **Settings > Swaparr**
2. The status display shows:
   - Currently striked downloads per application
   - Total downloads removed
   - Total downloads being tracked

### Resetting Strikes

If you need to reset the strike system:

1. Go to **Settings > Swaparr**
2. Click the **Reset** button in the status section
3. This will clear all tracked downloads and strikes
4. Confirm the action when prompted

### Understanding Logs

Swaparr-related log entries include:

- **INFO**: Normal operations like checks and strike assignments
- **WARNING**: Approaching strike limits
- **ACTION**: Removal of downloads that reached maximum strikes
- **ERROR**: Issues with download client communication

## Common Scenarios and Solutions

### Scenario: Too Many Removals

If Swaparr is removing too many downloads:

1. Enable **Dry Run Mode** temporarily
2. Increase **Maximum Strikes** (e.g., from 3 to 5)
3. Increase **Max Download Time** (e.g., from 2h to 4h)
4. Increase **Ignore Above Size** threshold

### Scenario: Not Removing Obvious Stalls

If Swaparr isn't removing clearly stalled downloads:

1. Decrease **Maximum Strikes** (e.g., from 5 to 3)
2. Decrease **Max Download Time** (e.g., from 4h to 2h)
3. Check logs for any errors in communication with download clients

### Scenario: Large Downloads Being Removed

If legitimate large downloads are being removed:

1. Significantly increase the **Ignore Above Size** setting
2. Consider your typical download sizes when setting this threshold

## Best Practices

### Finding the Right Balance

The ideal Swaparr configuration balances:

- Being aggressive enough to remove genuinely stuck downloads
- Being lenient enough to not interfere with legitimate slow downloads
- Accounting for your specific network conditions and media types

### Recommended for Most Users

For most users, these settings work well:

```yaml
swaparr:
  enabled: true
  max_strikes: 3
  max_download_time: 2h
  ignore_above_size: 25GB
  remove_from_client: true
  dry_run: false  # After initial testing period
```

### When to Enable Dry Run Mode

Enable Dry Run Mode when:

- First setting up Swaparr
- Making significant changes to Swaparr settings
- Troubleshooting issues with removals
- After changes to your download client configuration

## Troubleshooting

### Common Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| No stalled downloads detected | Criteria too lenient | Reduce max_download_time |
| Too many removals | Criteria too strict | Increase max_strikes or max_download_time |
| Legitimate downloads removed | Size threshold too low | Increase ignore_above_size |
| Not removing from client | Client communication issue | Check *arr application download settings |

### Fixing Client Connection Issues

If Swaparr isn't properly interacting with your download client:

1. Verify the download client settings in your *arr applications
2. Ensure the client is accessible from Huntarr
3. Check if the API or RPC interface of your client is enabled
4. Look for authentication issues in the logs

## Next Steps

With a properly configured Swaparr integration, consider exploring:

- [Multi-Instance Setup](multi-instance.md) to manage multiple download clients
- [Performance Tuning](../advanced/performance-tuning.md) for overall Huntarr optimization
- [API Rate Limiting](api-rate-limiting.md) to ensure stable operation 