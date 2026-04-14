#!/usr/bin/env bash
# Generate RS256 key pair for production JWT signing
set -euo pipefail

KEYS_DIR="${1:-.}"

echo "Generating RS256 key pair for JWT..."

# Generate private key
openssl genrsa -out "$KEYS_DIR/jwt-private.pem" 2048

# Extract public key
openssl rsa -in "$KEYS_DIR/jwt-private.pem" -pubout -out "$KEYS_DIR/jwt-public.pem"

echo ""
echo "Keys generated:"
echo "  Private: $KEYS_DIR/jwt-private.pem"
echo "  Public:  $KEYS_DIR/jwt-public.pem"
echo ""
echo "Add to .env:"
echo "  JWT_ALGORITHM=RS256"
echo "  JWT_PRIVATE_KEY=\$(cat $KEYS_DIR/jwt-private.pem)"
echo "  JWT_PUBLIC_KEY=\$(cat $KEYS_DIR/jwt-public.pem)"
echo ""
echo "WARNING: Keep jwt-private.pem SECRET. Never commit to git."
