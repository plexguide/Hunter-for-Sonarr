FROM python:3.9-slim

# Install required packages and dependencies
RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /config/stateful
RUN mkdir -p /config/log && chmod -R 755 /config/log && touch /config/log/huntarr.log


WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Set entry point
CMD ["python", "main.py"]