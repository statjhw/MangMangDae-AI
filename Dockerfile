# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# 1) Upgrade pip
# 2) Install CPU-only PyTorch first to avoid pulling CUDA wheels
# 3) Install sentence-transformers without extra deps (we provide transformers/torch separately)
# 4) Install remaining requirements from requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1 && \
    pip install --no-cache-dir sentence-transformers==2.7.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project (needed for Backend module imports)
COPY . .

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port (Railway will override this)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start the Backend application
CMD ["uvicorn", "Backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]