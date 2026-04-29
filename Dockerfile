# ── BackPocket API-only (no Flutter web build) ────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project source code
COPY . .

EXPOSE 8000

# Ensure run.sh is executable
RUN chmod +x run.sh

CMD ["./run.sh"]
