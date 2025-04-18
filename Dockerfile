FROM python:3.9-slim

WORKDIR /app

# Install required packages and dependencies including nano
RUN apt-get update && apt-get install -y \
    procps \
    nano \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /config/settings
RUN mkdir -p /config/logs
RUN mkdir -p /config/stateful
RUN chmod -R 755 /config

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_DIR=/config

# Expose port
EXPOSE 9705

# Make scripts executable
RUN chmod +x /app/scripts/*.sh
RUN chmod +x /app/scripts/orchestrator.sh
RUN mkdir -p /app/scripts/logs
RUN chmod +x /app/scripts/logs/*.sh

# Create service directories
RUN mkdir -p /app/services/sonarr
RUN mkdir -p /app/services/radarr
RUN mkdir -p /app/services/lidarr
RUN mkdir -p /app/services/readarr

# Make service scripts executable
RUN chmod +x /app/services/sonarr/sonarr.sh || true
RUN chmod +x /app/services/radarr/radarr.sh || true
RUN chmod +x /app/services/lidarr/lidarr.sh || true
RUN chmod +x /app/services/readarr/readarr.sh || true

# Make module scripts executable
RUN chmod +x /app/services/sonarr/missing.sh || true
RUN chmod +x /app/services/sonarr/upgrade.sh || true
RUN chmod +x /app/services/radarr/missing.sh || true
RUN chmod +x /app/services/radarr/upgrade.sh || true
RUN chmod +x /app/services/lidarr/missing.sh || true
RUN chmod +x /app/services/lidarr/upgrade.sh || true
RUN chmod +x /app/services/readarr/missing.sh || true
RUN chmod +x /app/services/readarr/upgrade.sh || true
RUN chmod +x /app/services/readarr/api_helper.sh || true

# Set entry point
CMD ["/app/scripts/start.sh"]