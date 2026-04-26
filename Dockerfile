FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow, chromadb, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


    