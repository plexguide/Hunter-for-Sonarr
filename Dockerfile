FROM python:3.9-slim

# Install system dependencies early
RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first to use Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create log directories at runtime (not build time)
RUN mkdir -p /config/stateful

# Set entry point
CMD ["python", "main.py"]
