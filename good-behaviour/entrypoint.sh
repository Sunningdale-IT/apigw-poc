#!/bin/bash
set -e

CERT_FILE="${MTLS_CERT_FILE:-/app/certs/server.crt}"
KEY_FILE="${MTLS_KEY_FILE:-/app/certs/server.key}"
CA_FILE="${MTLS_CA_FILE:-/app/certs/ca.crt}"

if [[ "${MTLS_ENABLED:-false}" == "true" ]]; then
    echo "Starting good-behaviour with mTLS on port 5443 (plain HTTP health on 5000)"

    if [[ ! -f "${CERT_FILE}" ]]; then
        echo "ERROR: mTLS enabled but server cert not found at ${CERT_FILE}" >&2
        exit 1
    fi
    if [[ ! -f "${KEY_FILE}" ]]; then
        echo "ERROR: mTLS enabled but server key not found at ${KEY_FILE}" >&2
        exit 1
    fi
    if [[ ! -f "${CA_FILE}" ]]; then
        echo "ERROR: mTLS enabled but CA cert not found at ${CA_FILE}" >&2
        exit 1
    fi

    # Run two gunicorn instances:
    #   - Port 5000: plain HTTP for Kubernetes liveness/readiness probes (health endpoint only)
    #   - Port 5443: HTTPS with mTLS for API traffic
    gunicorn \
        --bind "0.0.0.0:5443" \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --certfile "${CERT_FILE}" \
        --keyfile "${KEY_FILE}" \
        --ca-certs "${CA_FILE}" \
        --cert-reqs 2 \
        "goodbehaviour_project.wsgi:application" &

    gunicorn \
        --bind "0.0.0.0:5000" \
        --workers 1 \
        --threads 2 \
        --timeout 30 \
        "goodbehaviour_project.wsgi:application"
else
    echo "Starting good-behaviour in plain HTTP mode on port 5000"
    exec gunicorn \
        --bind "0.0.0.0:5000" \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        "goodbehaviour_project.wsgi:application"
fi
