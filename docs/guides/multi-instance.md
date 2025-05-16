# Multi-Instance Setup Guide

> This guide covers how to effectively configure and manage multiple instances of the same *arr application in Huntarr.

## Why Use Multiple Instances?

There are several reasons you might want to set up multiple instances of the same application:

- **Specialized Content**: Separate TV shows from anime, movies from documentaries
- **Different Quality Profiles**: One instance for 4K content, another for 1080p
- **Testing vs. Production**: Test new settings on one instance before applying to your main instance
- **Different Media Libraries**: Manage content for different users or locations

## Adding Multiple Instances

Huntarr supports up to 9 instances of each application type. Here's how to set them up:

1. Go to **Settings** and select the appropriate tab (Sonarr, Radarr, etc.)
2. Configure your first instance with all required details
3. Click the **Add Instance** button at the bottom of the form
4. Fill in the details for the new instance:
   - Give it a descriptive name that clearly identifies its purpose
   - Enter the URL and API key
   - Enable it if you want it to start processing immediately

![Multiple Instances Example](../assets/img/multi-instance-example.png)

## Configuration Strategies

### Scenario: TV Shows and Anime

For Sonarr, you might set up:

- **Instance 1: TV Shows**
  - Name: "Sonarr - TV Shows"
  - Standard TV show quality profiles
  - Higher search priority for current shows

- **Instance 2: Anime**
  - Name: "Sonarr - Anime"
  - Anime-specific quality profiles
  - Different search parameters for anime content

### Scenario: Movie Categories

For Radarr, consider:

- **Instance 1: General Movies**
  - Name: "Radarr - Movies"
  - Standard movie quality profiles
  
- **Instance 2: 4K Movies**
  - Name: "Radarr - 4K"
  - 4K-specific quality profiles
  - Higher resource allocation

## Balancing Resources

When running multiple instances, consider these tips for optimal performance:

- **Stagger Processing**: Set different sleep durations to avoid simultaneous searches
- **API Caps**: Distribute API caps based on priority and importance
- **Schedule Strategically**: Use scheduling to run less critical instances during off-hours

## Monitoring Multiple Instances

The Huntarr dashboard displays all configured instances, allowing you to:

- View connection status for each instance
- Monitor API usage per instance
- Track search and upgrade statistics independently

## Advanced Multi-Instance Setup

For more advanced setups, consider using:

- **Scheduling**: Different schedules for different instances
- **Stateful Management**: Shared tracking to prevent redundant searches
- **Specialized Settings**: Tailored settings for each instance's specific needs

## Next Steps

After setting up multiple instances, check out the [Scheduling Guide](scheduling.md) to learn how to optimize when each instance runs. 