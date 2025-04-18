FROM python:3.9-slim

WORKDIR /app

# Install required packages and dependencies
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /config/settings
RUN mkdir -p /config/logs
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

# Set entry point
CMD ["/app/scripts/start.sh"]