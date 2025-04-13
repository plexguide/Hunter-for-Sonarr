FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY src/primary/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /config/settings /config/stateful /config/user /tmp/huntarr-logs
RUN chmod -R 755 /config /tmp/huntarr-logs

# Set environment variables
ENV PYTHONPATH=/app
ENV APP_TYPE=sonarr

# Expose port
EXPOSE 9705

# Run start script
COPY primary/start.sh /app/start.sh
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]