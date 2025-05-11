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
RUN echo '#!/bin/sh\n\
# Ensure config permissions are correct on container restart\nif [ ! -f /config/.initialized ]; then\n  echo "Initializing Huntarr config directory..."\n  chown -R 1000:1000 /config\n  chmod -R 755 /config\n  touch /config/.initialized\nfi\n\n# Run the main application\nexec python3 /app/main.py\n' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_DIR=/config
ENV TZ=UTC

# Expose port
EXPOSE 9705

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]