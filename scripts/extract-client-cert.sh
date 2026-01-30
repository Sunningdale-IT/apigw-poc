#!/bin/bash
# Extract client certificate from Kubernetes secret
# Usage: ./extract-client-cert.sh [secret-name] [output-dir]
#
# This extracts the certificate, private key, and CA certificate
# from a Kubernetes secret for use by external clients.

set -euo pipefail

NAMESPACE="${NAMESPACE:-apigw-poc}"
SECRET_NAME="${1:-producer-mtls-client-cert}"
OUTPUT_DIR="${2:-./certs}"

echo "=============================================="
echo "  Extract Client Certificate"
echo "=============================================="
echo ""
echo "Namespace: ${NAMESPACE}"
echo "Secret: ${SECRET_NAME}"
echo "Output: ${OUTPUT_DIR}"
echo ""

# Check if secret exists
if ! kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" &>/dev/null; then
    echo "ERROR: Secret ${SECRET_NAME} not found in namespace ${NAMESPACE}"
    echo ""
    echo "Available secrets:"
    kubectl get secrets -n "${NAMESPACE}" | grep -E "(mtls|tls)" || echo "  (none found)"
    exit 1
fi

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Extract certificates
echo "Extracting certificates..."

# Client certificate
kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" \
    -o jsonpath='{.data.tls\.crt}' | base64 -d > "${OUTPUT_DIR}/client.crt"
echo "  - ${OUTPUT_DIR}/client.crt"

# Client private key
kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" \
    -o jsonpath='{.data.tls\.key}' | base64 -d > "${OUTPUT_DIR}/client.key"
chmod 600 "${OUTPUT_DIR}/client.key"
echo "  - ${OUTPUT_DIR}/client.key"

# CA certificate (from the CA secret)
if kubectl get secret mtls-ca-secret -n "${NAMESPACE}" &>/dev/null; then
    kubectl get secret mtls-ca-secret -n "${NAMESPACE}" \
        -o jsonpath='{.data.ca\.crt}' | base64 -d > "${OUTPUT_DIR}/ca.crt"
    echo "  - ${OUTPUT_DIR}/ca.crt"
else
    # Try to get CA from the client cert secret
    kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" \
        -o jsonpath='{.data.ca\.crt}' | base64 -d > "${OUTPUT_DIR}/ca.crt" 2>/dev/null || true
    if [[ -s "${OUTPUT_DIR}/ca.crt" ]]; then
        echo "  - ${OUTPUT_DIR}/ca.crt"
    else
        echo "  - WARNING: CA certificate not found"
    fi
fi

echo ""
echo "=============================================="
echo "  Certificate Details"
echo "=============================================="
echo ""

# Show certificate info
echo "Client Certificate:"
openssl x509 -in "${OUTPUT_DIR}/client.crt" -noout -subject -issuer -dates 2>/dev/null || echo "  (unable to parse)"
echo ""

# Verify certificate chain
if [[ -s "${OUTPUT_DIR}/ca.crt" ]]; then
    echo "Certificate Verification:"
    if openssl verify -CAfile "${OUTPUT_DIR}/ca.crt" "${OUTPUT_DIR}/client.crt" 2>/dev/null; then
        echo "  Certificate chain is valid!"
    else
        echo "  WARNING: Certificate verification failed"
    fi
fi

echo ""
echo "=============================================="
echo "  Usage Instructions"
echo "=============================================="
echo ""
echo "Use these files to make mTLS requests to Kong:"
echo ""
echo "  curl --cert ${OUTPUT_DIR}/client.crt \\"
echo "       --key ${OUTPUT_DIR}/client.key \\"
echo "       --cacert ${OUTPUT_DIR}/ca.crt \\"
echo "       https://kong.jim00.pd.test-rig.nl/consumer/api/consume"
echo ""
echo "Or run: ./scripts/test-mtls.sh --with-cert"
echo ""
