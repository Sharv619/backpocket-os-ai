#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BackPocket OS — Backup to Cloudflare R2
# Run via cron: 0 * * * * root /opt/backpocket/scripts/backup_to_r2.sh
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/var/lib/backpocket/backpocket.db}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/backpocket/backups}"
R2_BUCKET="${R2_BUCKET:-backpocket-backups}"
R2_ACCOUNT_ID="${R2_ACCOUNT_ID:-}"
R2_ACCESS_KEY="${R2_ACCESS_KEY:-}"
R2_SECRET_KEY="${R2_SECRET_KEY:-}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# ── Check prerequisites ──────────────────────────────────────────────────────
if [[ -z "$R2_ACCOUNT_ID" ]]; then
    echo "[WARN] R2 credentials not set, skipping upload"
    exit 0
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

# ── Upload to R2 ──────────────────────────────────────────────────
# Using AWS CLI with R2 (S3-compatible API)
export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$R2_SECRET_KEY"
export AWS_DEFAULT_REGION="auto"
export AWS_ENDPOINT_URL="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Upload
aws s3 cp "$BACKUP_FILE" "s3://${R2_BUCKET}/backpocket/${TIMESTAMP}.sql.gz" \
    --storage-class STANDARD_IA

# Cleanup local
rm -f "$BACKUP_FILE"

# ── Prune old backups ─────────────────────────────────────────────
find "$BACKUP_DIR" -name "backpocket_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup complete: backpocket_${TIMESTAMP}.sql.gz"

# ── Verify ───────────────────────────────────────────────────────
BACKUP_COUNT=$(aws s3 ls "s3://${R2_BUCKET}/backpocket/" | wc -l)
echo "R2 bucket contains $BACKUP_COUNT backups"