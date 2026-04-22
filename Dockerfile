FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow, chromadb, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

COPY run.sh .
CMD ["./run.sh"]
