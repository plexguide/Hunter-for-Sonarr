---
sidebar_position: 1
---

# Running Multiple Huntarr Instances

In some scenarios, you may want to run multiple instances of Huntarr to separate different types of media management or distribute the load. This guide explains how to set up and manage multiple Huntarr instances effectively.

## Use Cases for Multiple Instances

- **Separate media types**: Dedicate one instance to movies and another to TV shows
- **Testing configuration changes**: Run a test instance alongside your production instance
- **Different hunting profiles**: Use aggressive settings for some media and conservative settings for others
- **Distributed load**: Run instances on different machines to distribute system load

## Setting Up Multiple Instances

### Method 1: Using Different Container Names and Ports

The simplest approach is to run multiple Docker containers with different names, ports, and config volumes:

```bash
# First Huntarr instance (default)
docker run -d --name huntarr-main \
  --restart always \
  -p 9705:9705 \
  -v /your-path/huntarr-main:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest

# Second Huntarr instance
docker run -d --name huntarr-anime \
  --restart always \
  -p 9706:9705 \
  -v /your-path/huntarr-anime:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
```

This approach requires:
- Unique container names (e.g., `huntarr-main`, `huntarr-anime`)
- Different host ports (e.g., 9705, 9706)
- Separate configuration volumes

### Method 2: Using Docker Compose

For easier management, you can use Docker Compose to define all your instances:

```yaml
version: '3'
services:
  huntarr-movies:
    image: huntarr/huntarr:latest
    container_name: huntarr-movies
    restart: always
    ports:
      - "9705:9705"
    volumes:
      - /your-path/huntarr-movies:/config
    environment:
      - TZ=America/New_York

  huntarr-tv:
    image: huntarr/huntarr:latest
    container_name: huntarr-tv
    restart: always
    ports:
      - "9706:9705"
    volumes:
      - /your-path/huntarr-tv:/config
    environment:
      - TZ=America/New_York
```

Save this as `docker-compose.yml` and run:

```bash
docker-compose up -d
```

## Configuring Multiple Instances

Each instance should be configured independently:

1. Access each instance through its unique port (e.g., `http://YOUR_SERVER_IP:9705` and `http://YOUR_SERVER_IP:9706`)
2. Set up administrator accounts for each instance
3. Configure each instance with the specific *arr connections it should manage

### Recommended Configuration Strategy

For multiple instances, consider the following configuration strategy:

#### Instance 1: Movies
- Connect to Radarr instances
- Set a higher Hunt Missing value (e.g., 20)
- Set a moderate Sleep Duration (e.g., 15 minutes)

#### Instance 2: TV Shows
- Connect to Sonarr instances
- Set a moderate Hunt Missing value (e.g., 10)
- Set a higher Sleep Duration (e.g., 30 minutes)

This staggered approach ensures your instances aren't making API calls simultaneously, reducing the load on your systems and indexers.

## Monitoring Multiple Instances

To effectively monitor multiple Huntarr instances:

1. Use a browser with tabs for each instance's dashboard
2. Set up different notification settings for each instance if needed
3. Consider using a monitoring tool like Uptime Kuma to monitor the status of all instances

## Troubleshooting Multiple Instances

### Port Conflicts

If you see errors like `Error: listen EADDRINUSE: address already in use :::9705`:
- Ensure each instance uses a different host port
- Check if other applications are using your selected ports

### Network Issues

If instances can't connect to the same *arr applications:
- Verify network routing between containers
- Check for firewall rules that might be blocking specific container connections

### Resource Contention

If you notice performance issues:
- Stagger the Sleep Duration settings to prevent simultaneous processing
- Run instances on different hosts if experiencing resource constraints
- Reduce Hunt Missing and Hunt Upgrade values to lower the processing load 