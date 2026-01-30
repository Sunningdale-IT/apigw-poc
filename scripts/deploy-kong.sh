#!/bin/bash
#
# Deploy Kong API Gateway to Kubernetes
#
# This script deploys Kong using Helm and configures it to proxy
# requests to the Dogcatcher API with API key authentication.
#
# Usage:
#   ./deploy-kong.sh [OPTIONS]
#
# Options:
#   -n, --namespace       Kong namespace (default: kong)
#   -d, --dogcatcher-ns   Dogcatcher namespace (default: default)
#   -s, --dogcatcher-svc  Dogcatcher service name (default: dogcatcher-api)
#   --db                  Use PostgreSQL database mode (default: DB-less)
#   --generate-key        Generate and display API key for Model Citizen
#   -h, --help            Show this help message
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
KONG_NAMESPACE="kong"
DOGCATCHER_NAMESPACE="default"
DOGCATCHER_SERVICE="dogcatcher-api"
USE_DATABASE=false
GENERATE_KEY=false

# Colors for output
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
    head -20 "${BASH_SOURCE[0]}" | tail -16 | sed 's/^#//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--namespace)
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
            --db)
                USE_DATABASE=true
                shift
                ;;
            --generate-key)
                GENERATE_KEY=true
                shift
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
    
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

add_helm_repo() {
    log_info "Adding Kong Helm repository..."
    helm repo add kong https://charts.konghq.com 2>/dev/null || true
    helm repo update
    log_success "Helm repository updated"
}

create_namespace() {
    log_info "Creating namespace ${KONG_NAMESPACE}..."
    kubectl create namespace "${KONG_NAMESPACE}" 2>/dev/null || log_warn "Namespace already exists"
}

deploy_kong() {
    log_info "Deploying Kong to namespace ${KONG_NAMESPACE}..."
    
    local values_file
    values_file=$(mktemp)
    
    if [[ "${USE_DATABASE}" == true ]]; then
        cat > "${values_file}" << 'EOF'
ingressController:
  enabled: true
  installCRDs: false

proxy:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 80
    containerPort: 8000

admin:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 8001

postgresql:
  enabled: true
  auth:
    username: kong
    password: kong123
    database: kong

env:
  database: postgres
  pg_host: kong-postgresql
  pg_user: kong
  pg_password: kong123
  pg_database: kong
  plugins: bundled

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 512Mi
EOF
    else
        cat > "${values_file}" << 'EOF'
ingressController:
  enabled: true
  installCRDs: false

proxy:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 80
    containerPort: 8000

admin:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 8001

env:
  database: "off"
  plugins: bundled

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 512Mi
EOF
    fi
    
    helm upgrade --install kong kong/kong \
        --namespace "${KONG_NAMESPACE}" \
        --values "${values_file}" \
        --wait \
        --timeout 5m
    
    rm -f "${values_file}"
    log_success "Kong deployed successfully"
}

configure_kong_plugins() {
    log_info "Configuring Kong plugins..."
    
    kubectl apply -f - << EOF
---
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-key-auth
  namespace: ${KONG_NAMESPACE}
plugin: key-auth
config:
  key_names:
    - X-API-Key
    - apikey
  hide_credentials: true
---
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-rate-limit
  namespace: ${KONG_NAMESPACE}
plugin: rate-limiting
config:
  minute: 100
  policy: local
EOF
    
    log_success "Kong plugins configured"
}

configure_dogcatcher_route() {
    log_info "Configuring Dogcatcher API route..."
    
    kubectl apply -f - << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dogcatcher-api
  namespace: ${DOGCATCHER_NAMESPACE}
  annotations:
    konghq.com/plugins: dogcatcher-key-auth,dogcatcher-rate-limit
    konghq.com/strip-path: "true"
spec:
  ingressClassName: kong
  rules:
    - http:
        paths:
          - path: /dogcatcher
            pathType: Prefix
            backend:
              service:
                name: ${DOGCATCHER_SERVICE}
                port:
                  number: 5000
EOF
    
    log_success "Dogcatcher route configured"
}

create_consumer_and_key() {
    log_info "Creating Model Citizen consumer and API key..."
    
    # Generate API key
    local api_key
    api_key=$(openssl rand -hex 32)
    
    # Create consumer
    kubectl apply -f - << EOF
apiVersion: configuration.konghq.com/v1
kind: KongConsumer
metadata:
  name: model-citizen
  namespace: ${KONG_NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: kong
username: model-citizen
custom_id: model-citizen-app
credentials:
  - model-citizen-apikey
EOF
    
    # Create API key secret
    kubectl apply -f - << EOF
apiVersion: v1
kind: Secret
metadata:
  name: model-citizen-apikey
  namespace: ${KONG_NAMESPACE}
  labels:
    konghq.com/credential: key-auth
stringData:
  key: "${api_key}"
  kongCredType: key-auth
EOF
    
    log_success "Consumer and API key created"
    
    if [[ "${GENERATE_KEY}" == true ]]; then
        echo ""
        echo "=============================================="
        echo "  Model Citizen API Key (save this securely)"
        echo "=============================================="
        echo ""
        echo "  ${api_key}"
        echo ""
        echo "=============================================="
        echo ""
        echo "Use this key in the X-API-Key header when calling"
        echo "the Dogcatcher API through Kong."
        echo ""
    fi
}

print_summary() {
    echo ""
    log_success "Kong deployment complete!"
    echo ""
    log_info "Kong Services:"
    kubectl get svc -n "${KONG_NAMESPACE}" -l app.kubernetes.io/name=kong
    echo ""
    log_info "To test Kong proxy:"
    echo "  kubectl port-forward -n ${KONG_NAMESPACE} svc/kong-kong-proxy 8000:80"
    echo "  curl http://localhost:8000/dogcatcher/api/dogs/ -H 'X-API-Key: YOUR_KEY'"
    echo ""
    log_info "Kong Admin API:"
    echo "  kubectl port-forward -n ${KONG_NAMESPACE} svc/kong-kong-admin 8001:8001"
    echo "  curl http://localhost:8001/status"
    echo ""
    log_info "Model Citizen configuration:"
    echo "  API_GATEWAY_URL=http://kong-kong-proxy.${KONG_NAMESPACE}.svc.cluster.local/dogcatcher/api"
    echo ""
}

main() {
    parse_args "$@"
    
    echo ""
    log_info "Kong Deployment Configuration:"
    log_info "  Kong Namespace: ${KONG_NAMESPACE}"
    log_info "  Dogcatcher Namespace: ${DOGCATCHER_NAMESPACE}"
    log_info "  Dogcatcher Service: ${DOGCATCHER_SERVICE}"
    log_info "  Database Mode: ${USE_DATABASE}"
    echo ""
    
    check_prerequisites
    add_helm_repo
    create_namespace
    deploy_kong
    configure_kong_plugins
    configure_dogcatcher_route
    create_consumer_and_key
    print_summary
}

main "$@"
