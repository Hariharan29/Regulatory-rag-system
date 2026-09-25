# ── Stage: production image ──────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed by psycopg2 and PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port Uvicorn listens on
EXPOSE 8000

# Run the FastAPI app via Uvicorn
# host 0.0.0.0 is required to receive traffic from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
