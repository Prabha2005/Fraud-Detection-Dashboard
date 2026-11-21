# ==========================================
# FastAPI Backend Dockerfile
# Backend image for local Docker Compose deployment
# ==========================================

FROM python:3.11-slim

# Prevent Python from writing pyc files to disk and enable unbuffered console output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies:
# - libgomp1: required by XGBoost and SHAP OpenMP runtime
# - curl: required for the container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=600 --retries=10 -r requirements.txt

# Copy application source code and model artifacts
COPY . /app/

# Ensure runtime directories exist for SQLite database and audit logs
RUN mkdir -p /app/data /app/logs

# Expose default backend port
EXPOSE 8000

# Container healthcheck using the dedicated /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start Uvicorn ASGI server
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
