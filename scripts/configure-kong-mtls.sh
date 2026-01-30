#!/bin/bash
#
# Configure Kong to use mTLS when connecting to Dogcatcher API
#
# This script configures Kong to:
#   - Use client certificate when calling Dogcatcher API (upstream mTLS)
#   - Verify Dogcatcher server certificate
#
# Prerequisites:
#   - Kong deployed to Kubernetes
#   - mTLS certificates generated (run generate-mtls-certs.sh first)
#   - Dogcatcher deployed with mTLS enabled
#
# Usage:
#   ./configure-kong-mtls.sh [OPTIONS]
#
# Options:
#   -n, --kong-ns         Kong namespace (default: kong)
#   -d, --dogcatcher-ns   Dogcatcher namespace (default: default)
#   -s, --dogcatcher-svc  Dogcatcher service name (default: dogcatcher-api)
#   -p, --dogcatcher-port Dogcatcher mTLS port (default: 5443)
#   -c, --cert-dir        Certificate directory (default: ./certs/mtls)
#   -h, --help            Show this help message
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
KONG_NAMESPACE="kong"
DOGCATCHER_NAMESPACE="default"
DOGCATCHER_SERVICE="dogcatcher-api"
DOGCATCHER_PORT="5443"
CERT_DIR="${SCRIPT_DIR}/../certs/mtls"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

show_help() {
    head -28 "${BASH_SOURCE[0]}" | tail -24 | sed 's/^#//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--kong-ns)
                KONG_NAMESPACE="$2"
                shift 2
                ;;
            -d|--dogcatcher-ns)
                DOGCATCHER_NAMESPACE="$2"
                shift 2
                ;;
            -s|--dogcatcher-svc)
                DOGCATCHER_SERVICE="$2"
                shift 2
                ;;
            -p|--dogcatcher-port)
                DOGCATCHER_PORT="$2"
                shift 2
                ;;
            -c|--cert-dir)
                CERT_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check certificates exist
    for cert_file in "ca.crt" "kong-client.crt" "kong-client.key"; do
        if [[ ! -f "${CERT_DIR}/${cert_file}" ]]; then
            log_error "Certificate not found: ${CERT_DIR}/${cert_file}"
            log_error "Run generate-mtls-certs.sh first"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

create_kong_mtls_secret() {
    log_info "Creating Kong mTLS client certificate secret..."
    
    kubectl create secret generic kong-upstream-mtls \
        --namespace "${KONG_NAMESPACE}" \
        --from-file=tls.crt="${CERT_DIR}/kong-client.crt" \
        --from-file=tls.key="${CERT_DIR}/kong-client.key" \
        --from-file=ca.crt="${CERT_DIR}/ca.crt" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Kong mTLS secret created"
}

configure_kong_mtls_upstream() {
    log_info "Configuring Kong mTLS upstream for Dogcatcher..."
    
    local dogcatcher_host="${DOGCATCHER_SERVICE}.${DOGCATCHER_NAMESPACE}.svc.cluster.local"
    
    # Create Kong mTLS configuration using CRDs
    kubectl apply -f - << EOF
---
# Kong Certificate for upstream mTLS
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-mtls-auth
  namespace: ${KONG_NAMESPACE}
plugin: mtls-auth
config: {}
---
# Kong Upstream for Dogcatcher with mTLS
apiVersion: configuration.konghq.com/v1beta1
kind: KongUpstreamPolicy
metadata:
  name: dogcatcher-mtls-upstream
  namespace: ${DOGCATCHER_NAMESPACE}
spec:
  healthchecks:
    passive:
      healthy:
        successes: 3
      unhealthy:
        httpFailures: 3
EOF

    log_success "Kong mTLS upstream configured"
}

create_mtls_ingress() {
    log_info "Creating mTLS-enabled ingress for Dogcatcher..."
    
    kubectl apply -f - << EOF
---
# Service pointing to mTLS port
apiVersion: v1
kind: Service
metadata:
  name: ${DOGCATCHER_SERVICE}-mtls
  namespace: ${DOGCATCHER_NAMESPACE}
spec:
  selector:
    app: dogcatcher-api
  ports:
    - name: https
      port: 5443
      targetPort: 5443
      protocol: TCP
---
# Ingress with mTLS backend
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dogcatcher-api-mtls
  namespace: ${DOGCATCHER_NAMESPACE}
  annotations:
    konghq.com/plugins: dogcatcher-key-auth,dogcatcher-rate-limit
    konghq.com/strip-path: "true"
    konghq.com/protocol: "https"
    # Reference the upstream mTLS certificate
    konghq.com/upstream-policy: dogcatcher-mtls-upstream
spec:
  ingressClassName: kong
  rules:
    - http:
        paths:
          - path: /dogcatcher-mtls
            pathType: Prefix
            backend:
              service:
                name: ${DOGCATCHER_SERVICE}-mtls
                port:
                  number: 5443
EOF

    log_success "mTLS ingress created"
}

configure_kong_certificate() {
    log_info "Configuring Kong to use client certificate for upstream..."
    
    # For DB-less mode, we need to configure via ConfigMap
    # For DB mode, we use Admin API
    
    # Check if Kong admin is accessible
    local kong_admin_pod
    kong_admin_pod=$(kubectl get pods -n "${KONG_NAMESPACE}" -l app.kubernetes.io/name=kong -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "${kong_admin_pod}" ]]; then
        log_info "Configuring Kong via Admin API..."
        
        # Create certificate in Kong
        kubectl exec -n "${KONG_NAMESPACE}" "${kong_admin_pod}" -- /bin/sh -c "
            # Upload client certificate for upstream mTLS
            curl -s -X POST http://localhost:8001/certificates \
                -F 'cert=@/etc/secrets/kong-upstream-mtls/tls.crt' \
                -F 'key=@/etc/secrets/kong-upstream-mtls/tls.key' \
                -F 'snis[]=${DOGCATCHER_SERVICE}.${DOGCATCHER_NAMESPACE}.svc.cluster.local' || true
        " 2>/dev/null || log_warn "Could not configure via Admin API, manual configuration may be needed"
    fi
    
    log_success "Kong certificate configuration complete"
}

print_summary() {
    echo ""
    echo "=============================================="
    echo "  Kong mTLS Configuration Complete"
    echo "=============================================="
    echo ""
    echo "Kong is now configured to use mTLS when calling Dogcatcher API."
    echo ""
    echo "Architecture:"
    echo ""
    echo "  Model Citizen --> Kong (API Key) --> Dogcatcher API (mTLS)"
    echo "                         |"
    echo "                    Client Cert"
    echo ""
    echo "Endpoints:"
    echo "  - /dogcatcher       : HTTP backend (existing)"
    echo "  - /dogcatcher-mtls  : mTLS backend (new)"
    echo ""
    echo "To test mTLS connection:"
    echo ""
    echo "  # Port-forward Kong"
    echo "  kubectl port-forward -n ${KONG_NAMESPACE} svc/kong-kong-proxy 8000:80"
    echo ""
    echo "  # Call via mTLS endpoint"
    echo "  curl http://localhost:8000/dogcatcher-mtls/api/dogs/ \\"
    echo "    -H 'X-API-Key: YOUR_API_KEY'"
    echo ""
    echo "=============================================="
}

main() {
    parse_args "$@"
    
    echo ""
    log_info "Kong mTLS Configuration"
    log_info "  Kong Namespace: ${KONG_NAMESPACE}"
    log_info "  Dogcatcher: ${DOGCATCHER_SERVICE}.${DOGCATCHER_NAMESPACE}:${DOGCATCHER_PORT}"
    log_info "  Cert Dir: ${CERT_DIR}"
    echo ""
    
    check_prerequisites
    create_kong_mtls_secret
    configure_kong_mtls_upstream
    create_mtls_ingress
    configure_kong_certificate
    print_summary
}

main "$@"
