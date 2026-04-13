#!/usr/bin/env bash
# Database restore: download from MinIO → decrypt → pg_restore
# Usage: ./scripts/restore.sh <backup-filename>
set -euo pipefail

BACKUP_FILE=${1:?"Usage: restore.sh <backup-filename>"}
MINIO_BUCKET="${MINIO_BUCKET:-projex-backups}"

echo "═══════════════════════════════════════════"
echo "  ProjeX Suite Restore — $BACKUP_FILE"
echo "═══════════════════════════════════════════"

# 1. Download from MinIO
echo "[1/3] Downloading from MinIO..."
docker compose exec -T minio mc cp "local/$MINIO_BUCKET/$BACKUP_FILE" "/tmp/$BACKUP_FILE"
docker compose cp "minio:/tmp/$BACKUP_FILE" "/tmp/$BACKUP_FILE"

# 2. Decrypt if needed
RESTORE_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.gpg ]]; then
    echo "[2/3] Decrypting backup..."
    gpg --decrypt --output "/tmp/${BACKUP_FILE%.gpg}" "/tmp/$BACKUP_FILE"
    RESTORE_FILE="${BACKUP_FILE%.gpg}"
else
    echo "[2/3] No decryption needed"
fi

# 3. pg_restore
echo "[3/3] Restoring database..."
docker compose exec -T postgres pg_restore \
    -U "${POSTGRES_USER:-projex}" \
    -d "${POSTGRES_DB:-projex}" \
    --clean --if-exists \
    < "/tmp/$RESTORE_FILE"

# Cleanup
rm -f "/tmp/$BACKUP_FILE" "/tmp/$RESTORE_FILE"

echo ""
echo "✓ Restore complete from $BACKUP_FILE"
echo "═══════════════════════════════════════════"
