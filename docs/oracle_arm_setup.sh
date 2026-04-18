#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BackPocket OS — Oracle Cloud ARM Provisioning Script
# Target: Oracle Cloud "Always Free" ARM instance (Ampere A1)
# Run as: sudo bash oracle_arm_setup.sh
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERR]${NC} $1"; }

# ── Config ───────────────────────────────────────────────────────────────────
ADMIN_EMAIL="himanshu@backpocket.ai"
DOMAIN="api.backpocket.ai"
APP_DIR="/opt/backpocket"
DB_PATH="/var/lib/backpocket/backpocket.db"
OLLAMA_MODELS="llama3.1:8b-instruct llama3:8b-instruct gemma2:9b" # Ollama models to pull (separated by space)

# ── Check root ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
   log_err "Run as: sudo $0"
   exit 1
fi

log_info "BackPocket OS — Oracle ARM Setup"
log_info "────────────────────────────────"

# ── System update ───────────────────────────────────────────────────────
log_info "Updating system..."
apt update -qq
apt upgrade -y -qq
log_ok "System updated"

# ── Firewall ────────────────────────────────────────────────────────────────
log_info "Configuring firewall..."
apt install -y -qq ufw fail2ban

ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"

# Harden SSH
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload sshd
log_ok "Firewall configured"

# ── Install dependencies ─────────────────────────────────────────────────
log_info "Installing dependencies..."
apt install -y -qq \
    curl \
    git \
    nginx \
    certbot \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    build-essential \
    pkg-config \
    libssl-dev

# ══════════════════════════════════════════════════════���════════════════════
# Caddy (auto-TLS) — REPLACE nginx
# ═══════════════════════════════════════════════════════════════════════════
log_info "Installing Caddy..."
apt install -y -qq debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
apt update -qq
apt install -y -qq caddy
log_ok "Caddy installed"

# ── Caddy config ───────────────────────────────────────────────────
cat > /etc/caddy/Caddyfile << 'CADDYFILE'
{
    email himanshu@backpocket.ai # Use the specified email for Caddy
    auto_https off # Keep off for Certbot to manage TLS
}

api.backpocket.ai {
    reverse_proxy localhost:8000
    encode gzip zstd

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" # Added preload
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https: wss:; font-src 'self' data:; frame-ancestors 'none';" # More robust CSP
    }

    # Rate limiting
    rate_limit 100r/m

    # Access log
    log {
        output file /var/log/caddy/access.log
    }
}
CADDYFILE

# ── Install Ollama ───────────────────────────────────────────────────────
log_info "Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
log_info "Pulling Ollama models: $OLLAMA_MODELS"
for model in $OLLAMA_MODELS; do
    log_info "Pulling $model..."
    su -c "OLLAMA_HOST=127.0.0.1:11434 ollama pull $model" ubuntu || true
done

# ═══════════════════════════════════════════════════════════════════════════
# Python Environment
# ═══════════════════════════════════════════════════════════════════════════
log_info "Setting up Python..."

# Create venv
python3 -m venv /opt/backpocket/venv
source /opt/backpocket/venv/bin/activate

pip install --upgrade pip
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv
pip install httpx aiohttp cryptography pysqlite3

# Install backpocket deps
cd $APP_DIR
pip install -r requirements.txt || true

log_ok "Python environment ready"

# ═══════════════════════════════════════════════════════════════════════════
# Systemd Service
# ═══════════════════════════════════════════════════════════════════════════
log_info "Creating systemd service..."

cat > /etc/systemd/system/backpocket.service << 'SYSTEMD'
[Unit]
Description=BackPocket OS API
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/backpocket
Environment="PATH=/opt/backpocket/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/backpocket/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWriteDirectories=/var/lib/backpocket

[Install]
WantedBy=multi-user.target
SYSTEMD

systemctl daemon-reload
systemctl enable backpocket
log_ok "Systemd service created"

# ═══════════════════════════════════════════════════════════════════════════
# TLS (Let's Encrypt)
# ═══════════════════════════════════════════════════════════════════════════
log_info "Configure TLS..."
# Certbot will manage TLS, Caddy will proxy to Uvicorn
if [[ -n "$ADMIN_EMAIL" ]]; then
    # Ensure Nginx is not running before running certbot --nginx
    systemctl stop nginx || true # Stop nginx if it's running
    certbot --non-interactive --agree-tos --email "$ADMIN_EMAIL" --webroot -w /var/www/certbot -d "$DOMAIN" || log_warn "Certbot may require DNS A record and Caddy to be temporarily stopped or configured for webroot."
    # Restart Caddy to pick up new certificates, or ensure Caddy is set up to read them
    systemctl reload caddy
fi

# ═══════════════════════════════════════════════════════════════════════════
# Cron (backup)
# ═══════════════════════════════════════════════════════════════════════════
log_info "Setting up cron..."

# Create backup directory
mkdir -p /var/lib/backpocket/backups

# Hourly DB backup + R2 upload (see backup_to_r2.sh)
cat > /etc/cron.d/backpocket-backup << 'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 * * * * root /opt/backpocket/scripts/backup_to_r2.sh >> /var/log/backpocket-backup.log 2>&1
CRON

chmod 644 /etc/cron.d/backpocket-backup
systemctl reload cron
log_ok "Cron configured"

# ═══════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo "────────────────────────────────"
log_ok "Oracle ARM setup complete!"
log_info ""
log_info "NEXT STEPS:"
log_info "  1. Point DNS A record: $DOMAIN → $(hostname -I | awk '{print $1}')"
log_info "  2. Deploy code: rsync -av --exclude '.git' ./ ubuntu@$DOMAIN:/opt/backpocket/"
log_info "  3. Start service: systemctl start backpocket"
log_info "  4. Check: curl https://$DOMAIN/api/ping"
echo ""