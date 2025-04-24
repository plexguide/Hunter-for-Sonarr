FROM python:3.9-slim

WORKDIR /app

# Install required packages from the root requirements file
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /config/settings /config/stateful /config/user /config/logs
RUN chmod -R 755 /config

# Set environment variables
ENV PYTHONPATH=/app
# ENV APP_TYPE=sonarr # APP_TYPE is likely managed via config now, remove if not needed

# Expose port
EXPOSE 9705

# Run the main application using the new entry point
CMD ["python3", "main.py"]