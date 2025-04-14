FROM python:3.9-slim

WORKDIR /app

# Copy requirements first (for better caching)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /config/stateful /config/settings
RUN mkdir -p templates static/css static/js

# Copy application files
COPY src/main.py .
COPY src/start.sh .
COPY src/web_server.py .

# Ensure script is executable
RUN chmod +x start.sh

# Set up volumes and entrypoint
VOLUME /config
ENTRYPOINT ["./start.sh"]