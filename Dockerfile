# Dockerfile for Grok Crypto Super Intel (v3 packaging)
# Based on design: python:3.11-slim, copy, pip install, expose 8501, volume for data.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps if needed (minimal for streamlit/pandas etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create data dir (for persistence, reports, etc.)
RUN mkdir -p /app/data

# Expose Streamlit default port
EXPOSE 8501

# Volume for persistent data (portfolio_state.json, reports, backtest history, etc.)
VOLUME ["/app/data"]

# Set env for data dir (matches config)
ENV CRYPTO_INTEL_DATA_DIR=/app/data

# Default command: run the app
# Use --server.headless=true for container, --server.port=8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
