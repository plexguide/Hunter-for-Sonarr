FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY src/primary/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p /app/src/primary /app/frontend/templates /app/frontend/static/css /app/frontend/static/js /config/stateful /config/settings /config/user

# Copy application files
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY app.py .
COPY main.py .

# Default environment variables (minimal set)
ENV APP_TYPE="sonarr"

# Create volume mount points
VOLUME ["/config"]

# Expose web interface port
EXPOSE 9705

# Add startup script
COPY src/primary/start.sh .
RUN chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]