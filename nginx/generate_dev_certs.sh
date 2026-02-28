#!/bin/bash
# ============================================================
# Generate Self-Signed SSL Certificates for Development
# ============================================================
# Usage: bash generate_dev_certs.sh
# Output: nginx/certs/fullchain.pem, nginx/certs/privkey.pem
# ============================================================

set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate for development..."

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Engineering/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"

echo ""
echo "Certificates generated in $CERT_DIR/"
echo "  - fullchain.pem (certificate)"
echo "  - privkey.pem   (private key)"
echo ""
echo "WARNING: These are self-signed certs for DEVELOPMENT ONLY."
echo "Use proper CA-signed certificates (e.g., Let's Encrypt) in production."
