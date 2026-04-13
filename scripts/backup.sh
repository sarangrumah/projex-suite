#!/usr/bin/env bash
# Database backup: pg_dump → GPG encrypt → upload to MinIO
# Usage: ./scripts/backup.sh
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="projex-backup-$TIMESTAMP.sql.gz"
ENCRYPTED_FILE="$BACKUP_FILE.gpg"
MINIO_BUCKET="${MINIO_BUCKET:-projex-backups}"

echo "═══════════════════════════════════════════"
echo "  ProjeX Suite Backup — $TIMESTAMP"
echo "═══════════════════════════════════════════"

# 1. pg_dump
echo "[1/3] Dumping database..."
docker compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER:-projex}" \
    -d "${POSTGRES_DB:-projex}" \
    --format=custom \
    --compress=9 \
    > "/tmp/$BACKUP_FILE"

echo "  ✓ Dump size: $(du -h /tmp/$BACKUP_FILE | cut -f1)"

# 2. Encrypt with GPG
echo "[2/3] Encrypting backup..."
if [ -n "${GPG_RECIPIENT:-}" ]; then
    gpg --recipient "$GPG_RECIPIENT" --encrypt --output "/tmp/$ENCRYPTED_FILE" "/tmp/$BACKUP_FILE"
    rm "/tmp/$BACKUP_FILE"
    UPLOAD_FILE="$ENCRYPTED_FILE"
else
    echo "  ⚠ GPG_RECIPIENT not set — skipping encryption"
    UPLOAD_FILE="$BACKUP_FILE"
fi

# 3. Upload to MinIO
echo "[3/3] Uploading to MinIO..."
docker compose exec -T minio mc alias set local \
    http://localhost:9000 "${MINIO_ACCESS_KEY:-minioadmin}" "${MINIO_SECRET_KEY:-minioadmin}" 2>/dev/null || true
docker compose exec -T minio mc mb --ignore-existing "local/$MINIO_BUCKET" 2>/dev/null || true
docker compose cp "/tmp/$UPLOAD_FILE" minio:/tmp/
docker compose exec -T minio mc cp "/tmp/$UPLOAD_FILE" "local/$MINIO_BUCKET/$UPLOAD_FILE"

# Cleanup
rm -f "/tmp/$UPLOAD_FILE"

echo ""
echo "✓ Backup complete: $UPLOAD_FILE → MinIO/$MINIO_BUCKET"
echo "═══════════════════════════════════════════"
