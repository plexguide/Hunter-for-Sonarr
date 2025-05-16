# Frequently Asked Questions

## General Questions

### What is Huntarr?

Huntarr is an intelligent media hunting tool that works with your existing *arr applications (Sonarr, Radarr, Lidarr, Readarr, and Whisparr) to automatically search for missing and upgradable media in your libraries.

### How is Huntarr different from my existing *arr applications?

While the *arr applications monitor RSS feeds for new releases, they don't actively search for missing or upgradable content without manual intervention. Huntarr fills this gap by automating the search process, ensuring your library stays complete and high-quality.

### Does Huntarr download content directly?

No, Huntarr works as a coordinator that initiates searches in your existing *arr applications. The actual downloading is still handled by your *arr apps through their configured download clients (torrent clients or usenet downloaders).

### Which media applications are supported?

Huntarr currently supports:

- Sonarr (TV shows)
- Radarr (Movies)
- Lidarr (Music)
- Readarr (Books)
- Whisparr (Adult content)

### Does Huntarr support multiple instances of each application?

Yes, Huntarr supports up to 9 instances of each application type. This allows for specialized setups like separate Radarr instances for movies and documentaries, or different Sonarr instances for TV shows and anime.

## Configuration

### What are the recommended settings for a new user?

For new users, we recommend starting with conservative settings:

- **Missing Items to Search**: 1
- **Upgrade Items to Search**: 0 (until all missing content is found)
- **Sleep Duration**: 900 seconds (15 minutes)
- **API Cap - Hourly**: 20

After monitoring system performance and API usage, you can gradually adjust these settings.

### How do I determine the right API rate limits?

Most *arr applications don't have clearly documented API limits. As a general guideline:

- Start with 20 requests per hour
- Monitor for any rate-limiting errors in the logs
- Gradually increase if no issues occur

Self-hosted instances can typically handle higher limits than remotely hosted ones.

### What is stateful management and why is it important?

Stateful management tracks which media items Huntarr has already processed. This prevents the system from repeatedly searching for the same items, which would waste resources and potentially trigger API rate limits.

### Should I enable "Skip Future Releases"?

Yes, enabling "Skip Future Releases" is recommended for most users. This prevents Huntarr from searching for media that isn't available yet, such as movies still in theaters or TV episodes that haven't aired.

## Troubleshooting

### Why am I seeing "API connection error" messages?

API connection errors typically occur when:
- The URL is incorrect or inaccessible
- The API key is invalid
- The *arr application is not running
- There are network connectivity issues between Huntarr and the *arr application

Verify your connection settings and ensure the *arr application is accessible from the Huntarr container/system.

### How can I reduce API usage?

To reduce API usage:
- Increase the **Sleep Duration** between cycles
- Decrease the number of **Missing/Upgrade Items to Search**
- Use the scheduling feature to run searches during limited time periods
- Enable **Monitored Only** to focus only on content you care about

### Why are my statistics not updating?

If your statistics aren't updating, check:
- If the application is properly connected (status shows "Connected")
- If there are any error messages in the logs
- If the application has any missing content to process
- If your API limits have been reached

### What should I do if Huntarr is consuming too many resources?

If Huntarr is using excessive system resources:
- Increase the **Sleep Duration** between cycles
- Decrease the number of items searched per cycle
- Use scheduling to limit active hours
- Make sure only one instance of Huntarr is running

### How do I completely reset Huntarr?

To completely reset Huntarr:
1. Go to **Settings > General > Stateful Management**
2. Use the **Emergency Reset** button to clear processed items
3. Restart the Huntarr container or service

## Advanced Usage

### Can I prioritize certain applications over others?

Yes, you can prioritize by:
- Setting different **Missing Items to Search** values for each app
- Configuring different **Sleep Duration** periods
- Using the scheduling feature to allocate specific time slots to different apps

### How can I optimize Huntarr for a large media library?

For large libraries:
1. Start with the most important app and get it caught up first
2. Use higher search values initially to clear backlogs
3. Once caught up, reduce to maintenance levels
4. Consider running Huntarr on more powerful hardware

### Can Huntarr run in a low-resource environment?

Yes, Huntarr can run on systems with limited resources by:
- Setting longer sleep durations
- Searching fewer items per cycle
- Using scheduling to limit active hours
- Disabling apps you don't need to prioritize

### How do download limits work?

The **Maximum Download Queue Size** setting prevents Huntarr from initiating new downloads when your download client queue is full. Set this to a value that your system can comfortably handle to prevent overwhelming your download client.

### What is Swaparr and how does it integrate with Huntarr?

Swaparr is a companion tool that monitors and manages stalled downloads. It's integrated into Huntarr to help clean up stuck downloads by:
1. Monitoring downloads for stalled progress
2. Assigning "strikes" to downloads that remain stalled
3. Removing downloads that reach the maximum strike count

This helps maintain a healthy download queue without manual intervention.

## Misc Questions

### Is there a mobile app for Huntarr?

Currently, there is no dedicated mobile app for Huntarr. However, the web interface is mobile-responsive and works well on smartphone browsers.

### How often is Huntarr updated?

Huntarr follows a regular update schedule with:
- Bug fixes as needed
- Minor feature updates approximately monthly
- Major version updates several times a year

### How can I contribute to Huntarr?

You can contribute to the project by:
- Reporting bugs on the [GitHub issues page](https://github.com/plexguide/Huntarr.io/issues)
- Submitting feature requests
- Contributing code via pull requests
- Helping other users in the community forums

### Where can I get more help?

If you need additional assistance:
- Check the [GitHub discussions](https://github.com/plexguide/Huntarr.io/discussions)
- Join the [Discord server](https://discord.com/invite/PGJJjR5Cww)
- Post on the [Reddit community](https://www.reddit.com/r/huntarr/)

### Is Huntarr open source?

Yes, Huntarr is open source software released under the MIT License. You can view and contribute to the code on [GitHub](https://github.com/plexguide/Huntarr.io). 