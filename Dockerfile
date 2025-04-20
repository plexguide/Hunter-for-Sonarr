FROM python:3.9-slim

WORKDIR /app

# Install required packages and dependencies
RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /config/stateful
RUN chmod -R 755 /config
RUN mkdir -p /scripts

# Set environment variables with defaults
ENV PYTHONPATH=/app
ENV CONFIG_DIR=/config
ENV API_KEY=""
ENV API_URL="http://localhost:8989"
ENV API_TIMEOUT=60
ENV MONITORED_ONLY=true
ENV HUNT_MISSING_SHOWS=1
ENV HUNT_UPGRADE_EPISODES=0
ENV SLEEP_SECONDS=1500
ENV STATE_RESET_HOURS=168
ENV RANDOM_MISSING=true
ENV RANDOM_UPGRADES=true
ENV SKIP_FUTURE_EPISODES=true
ENV SKIP_SERIES_REFRESH=true
ENV COMMAND_WAIT_SECONDS=1
ENV COMMAND_WAIT_ATTEMPTS=600
ENV MINIMUM_DOWNLOAD_QUEUE_SIZE=-1

# Copy scripts
COPY scripts /scripts
RUN chmod -R +x /scripts

# Set entry point
ENTRYPOINT ["/scripts/start.sh"]