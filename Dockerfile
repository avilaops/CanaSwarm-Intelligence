# CanaSwarm Intelligence API - Docker Image
# 
# Build: docker build -t intelligence-api:latest .
# Run: docker run -p 6000:6000 intelligence-api:latest

FROM python:3.11-slim

# Install curl for healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY mocks/ ./mocks/
COPY data/ ./data/
COPY README.md .

# Create data directory for decisions storage
RUN mkdir -p /app/data

# Expose port
EXPOSE 6000

# Health check
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD curl -f http://localhost:6000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "6000"]
