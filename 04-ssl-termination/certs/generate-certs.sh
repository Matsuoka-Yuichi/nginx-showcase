#!/bin/bash
# Generate a self-signed certificate for the SSL termination demo.
# Run this script BEFORE starting docker-compose.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$SCRIPT_DIR/server.key" \
  -out "$SCRIPT_DIR/server.crt" \
  -subj "/C=US/ST=Workshop/L=Docker/O=Nginx Workshop/CN=localhost"

echo "Certificate generated:"
echo "  $SCRIPT_DIR/server.crt"
echo "  $SCRIPT_DIR/server.key"
