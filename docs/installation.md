# Installation Guide

There are several ways to install Huntarr depending on your preferences and system setup.

## Docker Installation (Recommended)

Docker is the simplest way to get Huntarr up and running without worrying about dependencies.

### Prerequisites

- Docker installed on your system
- Access to Docker Hub

### Basic Docker Run Command

```bash
docker run -d \
  --name=huntarr \
  -p 8123:8123 \
  -v /path/to/config:/config \
  --restart unless-stopped \
  plexguide/huntarr:latest
```

Replace `/path/to/config` with the path where you want to store Huntarr's configuration files.

### Docker Compose

For more advanced setups, you can use Docker Compose:

```yaml
version: '3'
services:
  huntarr:
    container_name: huntarr
    image: plexguide/huntarr:latest
    ports:
      - 8123:8123
    volumes:
      - /path/to/config:/config
    restart: unless-stopped
    environment:
      - TZ=Your/Timezone
```

Save this to a file named `docker-compose.yml` and run:

```bash
docker-compose up -d
```

## Native Installation

For users who prefer not to use Docker, you can install Huntarr directly on your system.

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/plexguide/Huntarr.io.git
cd Huntarr.io
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Start Huntarr:

```bash
python main.py
```

By default, Huntarr will be available at `http://localhost:8123`.

## Unraid Installation

Huntarr can be easily installed on Unraid using the Community Applications plugin.

1. Open the Unraid web interface
2. Navigate to the "Apps" tab
3. Search for "Huntarr"
4. Click "Install"
5. Configure the container settings as needed
6. Click "Apply"

## First-Time Setup

After installing Huntarr, you'll need to complete the initial setup:

1. Access the web interface at `http://your-ip:8123`
2. Create an admin account for secure access
3. Configure your *arr applications (Sonarr, Radarr, etc.)
4. Set up your hunting preferences and scheduling

## Updating Huntarr

### Docker Update

To update the Docker container:

```bash
# Pull the latest image
docker pull plexguide/huntarr:latest

# Stop and remove the current container
docker stop huntarr
docker rm huntarr

# Run a new container with the updated image
docker run -d \
  --name=huntarr \
  -p 8123:8123 \
  -v /path/to/config:/config \
  --restart unless-stopped \
  plexguide/huntarr:latest
```

With Docker Compose:

```bash
docker-compose pull
docker-compose up -d
```

### Native Update

For native installations:

```bash
cd Huntarr.io
git pull
pip install -r requirements.txt
```

## System Requirements

- **Minimum**: 1GB RAM, 1 CPU core, 1GB disk space
- **Recommended**: 2GB RAM, 2 CPU cores, 5GB disk space

## Troubleshooting

### Container won't start

Check the logs:

```bash
docker logs huntarr
```

### Connection issues

- Verify the port mappings are correct
- Check that your firewall isn't blocking the Huntarr port
- Ensure your *arr applications are accessible from the Huntarr container

### Permission issues

If you're having permission problems with the config directory:

```bash
sudo chown -R 1000:1000 /path/to/config
```

## Next Steps

Once you have Huntarr installed, head over to the [Configuration](configuration.md) guide to learn how to set up your media hunting preferences. 