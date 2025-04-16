FROM python:3.12-slim

WORKDIR /app

# Install dos2unix
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p /app/src /app/frontend/templates /app/frontend/static/css /app/frontend/static/js /config/stateful /config/settings /config/user

# Copy application files
COPY . .

# Default environment variables (minimal set)
ENV APP_TYPE="sonarr"

# Create volume mount points
VOLUME ["/config"]

# Expose web interface port
EXPOSE 9705

# Add startup script
COPY start.sh ./start.sh

# Convert Windows line endings to Unix just in case
RUN dos2unix ./start.sh

RUN chmod +x ./start.sh

# Run the startup script
CMD ["./start.sh"]