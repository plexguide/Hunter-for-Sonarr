---
sidebar_position: 2
---

# Installation Guide

Huntarr is distributed as a Docker container, making it easy to deploy on any system that supports Docker. This guide covers different installation methods.

## Installation Methods

### Docker Run

The simplest way to run Huntarr is via Docker (all configuration is done via the web UI):

```bash
# Option 1: DockerHub
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /your-path/huntarr:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest

# Option 2: GitHub Container Registry
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /your-path/huntarr:/config \
  -e TZ=America/New_York \
  ghcr.io/plexguide/huntarr:latest
```

To check on the status of the program, you can use the web interface at http://YOUR_SERVER_IP:9705 or check the logs with:

```bash
docker logs huntarr
```

### Docker Compose

For those who prefer Docker Compose, add this to your `docker-compose.yml` file:

```yaml
services:
  huntarr:
    # Option 1: DockerHub
    image: huntarr/huntarr:latest
    # Option 2: GitHub Container Registry
    # image: ghcr.io/plexguide/huntarr:latest
    container_name: huntarr
    restart: always
    ports:
      - "9705:9705"
    volumes:
      - /your-path/huntarr:/config
    environment:
      - TZ=America/New_York
```

Then run:

```bash
docker-compose up -d huntarr
```

### Unraid Users

You can install Huntarr using the Unraid App Store.

If not, you can run this from Command Line in Unraid:

```bash
# Option 1: DockerHub
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /mnt/user/appdata/huntarr:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
  
# Option 2: GitHub Container Registry
docker run -d --name huntarr \
  --restart always \
  -p 9705:9705 \
  -v /mnt/user/appdata/huntarr:/config \
  -e TZ=America/New_York \
  ghcr.io/plexguide/huntarr:latest
```

## Configuration After Installation

After installation, you'll need to:

1. Access the web interface at `http://YOUR_SERVER_IP:9705`
2. Set up your administrator account with optional 2FA
3. Configure connections to your *Arr applications
4. Adjust search settings for optimal performance

See the [Configuration Guide](configuration) for detailed setup instructions.

## Volume Mapping

To ensure data persistence, make sure you map the `/config` directory to a persistent volume on your host system:

```
-v /your-path/appdata/huntarr:/config
```

This directory will store your:
- User credentials
- Application settings
- Connection configurations
- Logs and state information

## Troubleshooting Installation Issues

If you encounter problems during installation:

- Make sure Docker is properly installed and running
- Verify the port 9705 is not already in use by another application
- Check that the volume mount path exists and has proper permissions
- Examine the container logs using `docker logs huntarr`
- Ensure your Docker host can access the internet to pull the image 