---
sidebar_position: 5
---

# Frequently Asked Questions

## General Questions

### What is Huntarr?
Huntarr is a specialized utility that automates discovering missing content and upgrading your existing media collection. It connects to your Sonarr, Radarr, Lidarr, Readarr, and Whisparr instances to help maintain your library.

### How does Huntarr work?
Huntarr connects to your *arr applications via their APIs, analyzes your libraries to find missing content and items below your quality cutoff, then initiates searches to fill these gaps or improve quality.

### Is Huntarr free to use?
Yes, Huntarr is free and open source software, released under the GPL-3.0 license.

### How often is Huntarr updated?
Huntarr receives regular updates to improve functionality and fix bugs. You can check the [GitHub releases page](https://github.com/plexguide/Huntarr.io/releases/) for the latest versions.

## Installation Questions

### What systems does Huntarr support?
Huntarr runs as a Docker container, so it can be deployed on any system that supports Docker, including Linux, macOS, Windows, and NAS devices like Unraid and Synology.

### What ports does Huntarr use?
Huntarr uses port 9705 by default for its web interface.

### Can I run Huntarr without Docker?
Docker is the recommended and officially supported deployment method, but since Huntarr is written in Python, advanced users could potentially run it directly from source.

## Configuration Questions

### Do I need to configure all *arr applications?
No, you can configure only the applications you use. Huntarr will only process the connections you've set up.

### How do I find my API keys?
API keys can be found in the Settings > General section of each *arr application:
- Sonarr: Settings > General > API Key
- Radarr: Settings > General > API Key
- Lidarr: Settings > General > API Key
- Readarr: Settings > General > API Key
- Whisparr: Settings > General > API Key

### What are the recommended settings for a large library?
For large libraries:
- Increase Sleep Duration to 1800-3600 seconds (30-60 minutes)
- Set Hunt Missing and Hunt Upgrades to 15-25 each
- Increase Minimum Download Queue Size to 10-15
- Enable Skip Series/Movie Refresh to reduce I/O
- Set API Hourly Cap based on your indexer's limits (typically 150-300)

### Can I use Huntarr with multiple instances of the same application?
Yes, you can configure multiple connections to the same type of application. This is useful if you have separate Sonarr instances for TV shows and anime, for example.

## Usage Questions

### Will Huntarr overwhelm my indexers?
No, Huntarr includes sophisticated API rate management that prevents overwhelming your indexers. You can configure the API hourly cap to match your indexer's rate limits.

### How can I tell if Huntarr is working?
The Huntarr dashboard shows statistics on missing content and upgrade hunts. You can also check the logs to see detailed information about each hunt cycle.

### Can I temporarily disable hunting?
Yes, you can pause hunting on the Settings page. Huntarr will complete its current cycle and then pause until you enable hunting again.

### How does Huntarr handle future releases?
By default, Huntarr skips items with future release dates to avoid unnecessary API calls. This can be disabled in settings if needed.

## Troubleshooting

### Huntarr can't connect to my *arr application
Check the following:
- Verify the URL is correct and includes the protocol (http/https) and port
- Ensure there is no trailing slash in the URL
- Double-check your API key
- Confirm network connectivity between Huntarr and the application
- Verify your *arr application is up and running

### API calls keep failing
If API calls consistently fail:
- Enable Debug Mode to see detailed API responses
- Check if your *arr application is rate-limiting requests
- Verify your network doesn't have firewall rules blocking the connections
- Increase the Universal API Timeout if your server is slower

### Huntarr isn't finding any missing content
This could be because:
- Your library is already complete (congratulations!)
- You have "Skip Future Items" enabled and the content has future release dates
- The items aren't marked as monitored in your *arr application
- Your search criteria in the *arr application are too restrictive

### Huntarr is using too many API calls
To reduce API usage:
- Increase the Sleep Duration between hunt cycles
- Decrease the Hunt Missing and Hunt Upgrades values
- Enable Skip Series/Movie Refresh to avoid unnecessary refreshes
- Lower the API Hourly Cap to a more conservative value 