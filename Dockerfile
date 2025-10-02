FROM python:3.10-slim

# Install system dependencies including git and build tools
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Expose port (Railway will override with PORT env var)
EXPOSE 8080

# Start the server
CMD ["python", "start_server.py"]
