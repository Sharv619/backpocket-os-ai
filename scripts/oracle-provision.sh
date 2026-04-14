#!/bin/bash
# BackPocket OS — Oracle Cloud ARM Provisioning Script
# Run this on a fresh Oracle Cloud ARM Ampere A1 instance
# This script sets up: FastAPI + PostgreSQL + Ollama + Caddy

set -e

echo "=========================================="
echo "BackPocket OS — Oracle ARM Setup"
echo "=========================================="

# ── Colors ──────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Update & Install ────────────────────────────
echo -e "${YELLOW}[1/8] Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

# ── Install Python & pip ─────────────────────────
echo -e "${YELLOW}[2/8] Installing Python...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget

# ── Install PostgreSQL ───────────────────────────
echo -e "${YELLOW}[3/8] Installing PostgreSQL...${NC}"
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER backpocket WITH PASSWORD 'backpocket123';" || true
sudo -u postgres psql -c "CREATE DATABASE backpocket OWNER backpocket;" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE backpocket TO backpocket;" || true

# Enable pgvector extension
sudo -u postgres psql -d backpocket -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

# ── Install Caddy (Reverse Proxy) ────────────────
echo -e "${YELLOW}[4/8] Installing Caddy...${NC}"
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.com/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.com/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/caddy-stable.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.com/public/caddy/stable/deb stable main" | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

# ── Install Ollama (Local AI) ────────────────────
echo -e "${YELLOW}[5/8] Installing Ollama...${NC}"
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b || echo "Ollama pull skipped for now"

# ── Clone & Setup BackPocket ─────────────────────
echo -e "${YELLOW}[6/8] Setting up BackPocket...${NC}"
cd /opt
sudo git clone https://github.com/Sharv619/backpocket-os-ai.git backpocket || sudo git -C /opt/backpocket pull
cd /opt/backpocket

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv

# Set environment variables
echo "DATABASE_URL=postgresql://backpocket:backpocket123@localhost:5432/backpocket" >> .env
echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env

# ── Create Systemd Service ────────────────────────
echo -e "${YELLOW}[7/8] Creating systemd service...${NC}"
sudo tee /etc/systemd/system/backpocket.service > /dev/null <<'EOF'
[Unit]
Description=BackPocket OS API
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/backpocket
Environment="PATH=/opt/backpocket/venv/bin"
ExecStart=/opt/backpocket/venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable backpocket
sudo systemctl start backpocket

# ── Configure Caddy ──────────────────────────────
echo -e "${YELLOW}[8/8] Configuring Caddy...${NC}"
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
:80 {
    reverse_proxy localhost:8000
    encode gzip
    log {
        output file /var/log/caddy/access.log
    }
}
EOF

sudo systemctl reload caddy

# ── Done ─────────────────────────────────────────
echo ""
echo -e "${GREEN}=========================================="
echo "✅ BackPocket OS is ready!"
echo "==========================================${NC}"
echo ""
echo "🔗 Backend API: http://YOUR_ORACLE_IP"
echo "🔗 (Add Cloudflare Tunnel for HTTPS)"
echo ""
echo "Services running:"
echo "  - FastAPI: http://127.0.0.1:8000"
echo "  - PostgreSQL: postgresql://backpocket:backpocket123@localhost:5432/backpocket"
echo "  - Ollama: http://localhost:11434"
echo "  - Caddy: http://YOUR_ORACLE_IP:80"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status backpocket   # Check API"
echo "  sudo journalctl -u backpocket -f   # View logs"
echo "  ollama list                         # Check models"
echo ""
echo "Next step: Set up Cloudflare Tunnel"
echo "  ~/cloudflared tunnel --url http://127.0.0.1:8000"