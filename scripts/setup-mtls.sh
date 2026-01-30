#!/bin/bash
# Setup mTLS for Kong API Gateway
# This script configures mutual TLS between Producer (3rd party) and Consumer (home party)
#
# Prerequisites:
# - cert-manager installed on the cluster
# - apigw-poc Helm release deployed
# - kubectl configured with cluster access

set -euo pipefail

NAMESPACE="${NAMESPACE:-apigw-poc}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="${SCRIPT_DIR}/../k8s-manifests/mtls"

echo "=============================================="
echo "  mTLS Setup for Kong API Gateway"
echo "=============================================="
echo ""
echo "Namespace: ${NAMESPACE}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! kubectl get namespace "${NAMESPACE}" &>/dev/null; then
    echo "ERROR: Namespace ${NAMESPACE} does not exist."
    echo "Please deploy the Helm chart first: helm install apigw-poc ./helm-chart/apigw-poc -n ${NAMESPACE} --create-namespace"
    exit 1
fi

if ! kubectl get pods -n cert-manager &>/dev/null; then
    echo "ERROR: cert-manager namespace not found."
    echo "Please install cert-manager first: https://cert-manager.io/docs/installation/"
    exit 1
fi

echo "Prerequisites OK"
echo ""

# Step 1: Create the mTLS CA
echo "Step 1: Creating mTLS Certificate Authority..."
kubectl apply -f "${MANIFESTS_DIR}/01-mtls-ca.yaml"

# Wait for CA certificate to be ready
echo "Waiting for CA certificate to be issued..."
for i in {1..30}; do
    if kubectl get secret mtls-ca-secret -n "${NAMESPACE}" &>/dev/null; then
        echo "CA certificate ready!"
        break
    fi
    if [[ "${i}" -eq 30 ]]; then
        echo "ERROR: Timeout waiting for CA certificate"
        kubectl describe certificate mtls-ca -n "${NAMESPACE}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""

# Step 2: Issue Producer client certificate
echo "Step 2: Issuing Producer client certificate..."
kubectl apply -f "${MANIFESTS_DIR}/02-producer-client-cert.yaml"

# Wait for client certificate to be ready
echo "Waiting for client certificate to be issued..."
for i in {1..30}; do
    if kubectl get secret producer-mtls-client-cert -n "${NAMESPACE}" &>/dev/null; then
        READY=$(kubectl get certificate producer-mtls-client -n "${NAMESPACE}" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
        if [[ "${READY}" == "True" ]]; then
            echo "Client certificate ready!"
            break
        fi
    fi
    if [[ "${i}" -eq 30 ]]; then
        echo "ERROR: Timeout waiting for client certificate"
        kubectl describe certificate producer-mtls-client -n "${NAMESPACE}"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""

# Step 3: (Optional) Patch Kong deployment to mount CA certificate for enforcement
echo "Step 3: Certificate infrastructure complete."
echo ""
echo "NOTE: To enforce mTLS (require client certificates), apply the Kong patch:"
echo "  kubectl apply -f k8s-manifests/mtls/03-kong-mtls-config.yaml"

echo ""
echo "=============================================="
echo "  mTLS Setup Complete!"
echo "=============================================="
echo ""
echo "Certificates created:"
kubectl get certificates -n "${NAMESPACE}"
echo ""
echo "Secrets created:"
kubectl get secrets -n "${NAMESPACE}" | grep -E "(mtls|tls)"
echo ""
echo "Next steps:"
echo "1. Extract client certificate: ./scripts/extract-client-cert.sh"
echo "2. Test mTLS connection: ./scripts/test-mtls.sh"
echo ""
