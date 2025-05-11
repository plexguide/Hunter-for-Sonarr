FROM python:3.9-slim

WORKDIR /app

# Install system dependencies and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install required packages from the root requirements file
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create all necessary config directories with appropriate permissions
RUN mkdir -p /config/settings \
    /config/db \
    /config/logs \
    /config/stateful \
    /config/user \
    /config/backups \
    && touch /config/logs/huntarr.log \
    && touch /config/logs/api_errors.log \
    && touch /config/logs/windows_service.log \
    && chown -R 1000:1000 /config \
    && chmod -R 755 /config

# Create a proper entrypoint script to handle initialization
RUN echo '#!/bin/sh' > /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Ensure config permissions are correct on container restart' >> /app/entrypoint.sh && \
    echo 'if [ ! -f /config/.initialized ]; then' >> /app/entrypoint.sh && \
    echo '  echo "Initializing Huntarr config directory..."' >> /app/entrypoint.sh && \
    echo '  chown -R 1000:1000 /config' >> /app/entrypoint.sh && \
    echo '  chmod -R 755 /config' >> /app/entrypoint.sh && \
    echo '  touch /config/.initialized' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Run the main application' >> /app/entrypoint.sh && \
    echo 'exec python3 /app/main.py' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_DIR=/config
ENV TZ=UTC

# Expose port
EXPOSE 9705

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]