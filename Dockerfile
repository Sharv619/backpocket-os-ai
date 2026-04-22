FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow, chromadb, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Flutter SDK
# Specify a Flutter version
ENV FLUTTER_VERSION=3.22.0
ENV PATH="$PATH:/opt/flutter/bin"
RUN git clone https://github.com/flutter/flutter.git /opt/flutter \
    && /opt/flutter/bin/git checkout $FLUTTER_VERSION \
    && /opt/flutter/bin/flutter precache \
    && /opt/flutter/bin/flutter doctor

# Build Flutter web app
# Assuming flutter_prototype/backpocket_mobile is your Flutter project root
WORKDIR /app/flutter_prototype/backpocket_mobile
RUN flutter build web --release

# Switch back to the /app directory
WORKDIR /app

# Copy built Flutter web assets to static_flutter
COPY --from=0 /app/flutter_prototype/backpocket_mobile/build/web ./static_flutter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

COPY run.sh .
CMD ["./run.sh"]
