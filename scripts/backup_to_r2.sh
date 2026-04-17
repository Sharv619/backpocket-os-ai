#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BackPocket OS — Backup to Cloudflare R2
# Run via cron: 0 * * * * root /opt/backpocket/scripts/backup_to_r2.sh
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $(date +%H:%M:%S) $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $(date +%H:%M:%S) $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date +%H:%M:%S) $1"; }
log_err() { echo -e "${RED}[ERR]${NC} $(date +%H:%M:%S) $1"; }

# ── Config ─────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/var/www/backpocket-mvp/backpocket.db}" # Updated to reflect app deployment directory
BACKUP_DIR="${BACKUP_DIR:-/var/backpocket_backups}" # Changed to a more standard backup location
R2_BUCKET="${R2_BUCKET:-backpocket-prod-backups}" # Specific bucket name
R2_ACCOUNT_ID="${R2_ACCOUNT_ID:-<YOUR_CLOUDFLARE_ACCOUNT_ID>}" # Placeholder for account ID
R2_ACCESS_KEY="${R2_ACCESS_KEY:-<YOUR_R2_ACCESS_KEY_ID>}" # Placeholder for R2 Access Key
R2_SECRET_KEY="${R2_SECRET_KEY:-<YOUR_R2_SECRET_ACCESS_KEY>}" # Placeholder for R2 Secret Key
RETENTION_DAYS="${RETENTION_DAYS:-7}" # Keep last 7 days of backups locally

# ── Check prerequisites ──────────────────────────────────────────────────────
if [[ -z "$R2_ACCOUNT_ID" || -z "$R2_ACCESS_KEY" || -z "$R2_SECRET_KEY" ]]; then
    log_warn "R2 credentials not fully set (R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY). Skipping R2 upload."
    # Proceed with local backup if R2 credentials are missing
    SKIP_R2_UPLOAD=true
else
    SKIP_R2_UPLOAD=false
fi

# ── Create backup ──────────────────────────────────────────────────────
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backpocket_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

# Dump SQLite
sqlite3 "$DB_PATH" ".dump" > "$BACKUP_FILE"

# Compress
gzip -f "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

if [ "$SKIP_R2_UPLOAD" = false ]; then
    log_info "Starting R2 upload..."
    # Using AWS CLI with R2 (S3-compatible API)
    export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$R2_SECRET_KEY"
    export AWS_DEFAULT_REGION="auto"
    export AWS_ENDPOINT_URL="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    # Upload
    aws s3 cp "$BACKUP_FILE" "s3://${R2_BUCKET}/backpocket/${TIMESTAMP}.sql.gz" \
        --storage-class STANDARD_IA
    
    log_ok "Uploaded backpocket_${TIMESTAMP}.sql.gz to R2"
    
    # Verify R2 backup count (optional, can be slow)
    BACKUP_COUNT=$(aws s3 ls "s3://${R2_BUCKET}/backpocket/" --endpoint-url="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com" | wc -l)
    log_info "R2 bucket contains $BACKUP_COUNT backups"
else
    log_warn "R2 upload skipped due to missing credentials."
fi

# ── Local Cleanup ──────────────────────────────────────────────────
log_info "Cleaning up local files..."
rm -f "$BACKUP_FILE" # Remove the compressed dump file
find "$BACKUP_DIR" -name "backpocket_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
log_ok "Local cleanup complete. Backups older than ${RETENTION_DAYS} days removed."

log_ok "BackPocket OS R2 backup script finished successfully."