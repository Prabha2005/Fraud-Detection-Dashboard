# ==========================================
# Streamlit Dashboard Frontend Dockerfile
# Frontend image for local Docker Compose deployment
# ==========================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install frontend requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --default-timeout=600 --retries=10 -r requirements.txt

# Copy frontend application code and assets
COPY . /app/

# Expose Streamlit port
EXPOSE 8501

# Container healthcheck using Streamlit core health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit app
CMD ["streamlit", "run", "ui.py"]
