#!/bin/bash
# Enable mTLS enforcement on Kong routes
# This configures Traefik to require client certificates for the /consumer route
#
# Usage: ./enable-mtls-enforcement.sh [enable|disable|status]

set -euo pipefail

NAMESPACE="${NAMESPACE:-apigw-poc}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="${SCRIPT_DIR}/../k8s-manifests/mtls"

ACTION="${1:-status}"

print_header() {
    echo ""
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
    echo ""
}

check_prerequisites() {
    # Check if mTLS CA exists
    if ! kubectl get secret mtls-ca-secret -n "${NAMESPACE}" &>/dev/null; then
        echo "ERROR: mTLS CA secret not found."
        echo "Run ./scripts/setup-mtls.sh first to create the certificate infrastructure."
        exit 1
    fi
    
    # Check if Traefik CRDs are available
    if ! kubectl get crd ingressroutes.traefik.io &>/dev/null; then
        echo "ERROR: Traefik CRDs not found."
        echo "This script requires Traefik ingress controller with CRDs installed."
        exit 1
    fi
}

enable_mtls() {
    print_header "Enabling mTLS Enforcement"
    
    check_prerequisites
    
    echo "Applying Traefik mTLS configuration..."
    kubectl apply -f "${MANIFESTS_DIR}/04-traefik-mtls-enforcement.yaml"
    
    echo ""
    echo "Disabling standard Kong ingress (replaced by IngressRoute)..."
    kubectl annotate ingress kong-ingress -n "${NAMESPACE}" \
        traefik.ingress.kubernetes.io/router.tls.options="" --overwrite 2>/dev/null || true
    
    echo ""
    echo "mTLS enforcement ENABLED on /consumer route"
    echo ""
    echo "Test commands:"
    echo "  # Should FAIL (no cert):"
    echo "  curl https://kong.jim00.pd.test-rig.nl/consumer/api/consume"
    echo ""
    echo "  # Should SUCCEED (with cert):"
    echo "  ./scripts/test-mtls.sh --with-cert"
}

disable_mtls() {
    print_header "Disabling mTLS Enforcement"
    
    echo "Removing Traefik mTLS configuration..."
    kubectl delete -f "${MANIFESTS_DIR}/04-traefik-mtls-enforcement.yaml" 2>/dev/null || true
    
    echo ""
    echo "mTLS enforcement DISABLED"
    echo "All requests will be accepted (with or without client certificate)"
}

show_status() {
    print_header "mTLS Enforcement Status"
    
    echo "Namespace: ${NAMESPACE}"
    echo ""
    
    echo "Certificate Infrastructure:"
    kubectl get certificates -n "${NAMESPACE}" 2>/dev/null | grep -E "(NAME|mtls)" || echo "  No mTLS certificates found"
    echo ""
    
    echo "Traefik mTLS Resources:"
    if kubectl get tlsoption mtls-strict -n "${NAMESPACE}" &>/dev/null; then
        echo "  TLSOption 'mtls-strict': CONFIGURED"
        kubectl get tlsoption mtls-strict -n "${NAMESPACE}" -o jsonpath='  Client Auth Type: {.spec.clientAuth.clientAuthType}' 2>/dev/null
        echo ""
    else
        echo "  TLSOption 'mtls-strict': NOT CONFIGURED"
    fi
    
    if kubectl get ingressroute kong-mtls-route -n "${NAMESPACE}" &>/dev/null; then
        echo "  IngressRoute 'kong-mtls-route': CONFIGURED (mTLS ENFORCED)"
    else
        echo "  IngressRoute 'kong-mtls-route': NOT CONFIGURED (mTLS NOT ENFORCED)"
    fi
    echo ""
    
    echo "Quick Test:"
    echo "  Running connection test without certificate..."
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://kong.jim00.pd.test-rig.nl/consumer/api/consume" 2>/dev/null || echo "000")
    
    if [[ "${HTTP_CODE}" == "200" ]]; then
        echo "  Result: 200 OK - mTLS is NOT enforced (requests without certs accepted)"
    elif [[ "${HTTP_CODE}" == "400" ]] || [[ "${HTTP_CODE}" == "403" ]] || [[ "${HTTP_CODE}" == "421" ]]; then
        echo "  Result: ${HTTP_CODE} - mTLS IS enforced (requests without certs rejected)"
    else
        echo "  Result: ${HTTP_CODE} - Unable to determine (may be network issue)"
    fi
}

case "${ACTION}" in
    enable)
        enable_mtls
        ;;
    disable)
        disable_mtls
        ;;
    status|*)
        show_status
        ;;
esac
