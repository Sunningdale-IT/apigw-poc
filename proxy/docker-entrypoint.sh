#!/bin/bash
#
# Docker entrypoint for Dogcatcher Proxy
#
# Environment variables:
#   PROXY_MODE: "dev" or "prod" (default: dev)
#   DOMAIN: Domain name for Let's Encrypt (required for prod)
#   EMAIL: Email for Let's Encrypt notifications
#   ENABLE_HTTPS: "true" or "false" (default: false)
#   ENABLE_MTLS: "true" or "false" (default: false)
#   CA_CERT_PATH: Path to CA certificate for mTLS
#

set -e

PROXY_MODE="${PROXY_MODE:-dev}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
ENABLE_MTLS="${ENABLE_MTLS:-false}"

echo "=============================================="
echo "  Dogcatcher API Gateway Proxy"
echo "=============================================="
echo "  Mode: ${PROXY_MODE}"
echo "  HTTPS: ${ENABLE_HTTPS}"
echo "  mTLS: ${ENABLE_MTLS}"
echo "=============================================="

# Select configuration based on mode
if [[ "${PROXY_MODE}" == "prod" ]]; then
    echo "Using production configuration..."
    cp /etc/nginx/nginx.conf.prod /etc/nginx/nginx.conf
else
    echo "Using development configuration..."
    # nginx-dev.conf is already the default
fi

# Setup certificates for HTTPS
if [[ "${ENABLE_HTTPS}" == "true" ]]; then
    if [[ -z "${DOMAIN}" ]]; then
        echo "WARNING: HTTPS enabled but DOMAIN not set. Using self-signed certificate."
    elif [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
        echo "Using existing Let's Encrypt certificate for ${DOMAIN}"
        ln -sf "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" /etc/nginx/certs/server.crt
        ln -sf "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" /etc/nginx/certs/server.key
    else
        echo "Let's Encrypt certificate not found. Using self-signed certificate."
        echo "Run 'docker exec <container> certbot-init.sh' to obtain Let's Encrypt certificate."
    fi
fi

# Setup CA certificate for mTLS
if [[ "${ENABLE_MTLS}" == "true" ]]; then
    if [[ -n "${CA_CERT_PATH}" ]] && [[ -f "${CA_CERT_PATH}" ]]; then
        echo "Using CA certificate from ${CA_CERT_PATH}"
        cp "${CA_CERT_PATH}" /etc/nginx/certs/ca.crt
    else
        echo "WARNING: mTLS enabled but CA_CERT_PATH not set or file not found."
        echo "Using placeholder CA certificate."
    fi
fi

# Validate nginx configuration
echo "Validating nginx configuration..."
nginx -t

# Execute the main command
exec "$@"
