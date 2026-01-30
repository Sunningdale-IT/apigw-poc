#!/bin/bash
#
# Generate mTLS certificates for Dogcatcher API
#
# This script creates:
#   - CA certificate (self-signed root CA)
#   - Server certificate for Dogcatcher API
#   - Client certificate for Kong API Gateway
#
# Usage:
#   ./generate-mtls-certs.sh [OPTIONS]
#
# Options:
#   -o, --output-dir    Output directory for certificates (default: ./certs)
#   -d, --days          Certificate validity in days (default: 365)
#   -c, --cn            Common Name for server cert (default: dogcatcher-api)
#   --san               Subject Alternative Names (default: localhost,dogcatcher-api)
#   -h, --help          Show this help message
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
OUTPUT_DIR="${SCRIPT_DIR}/../certs/mtls"
VALIDITY_DAYS=365
SERVER_CN="dogcatcher-api"
SUBJECT_ALT_NAMES="localhost,dogcatcher-api,dogcatcher-web,dogcatcher-api.default.svc.cluster.local"

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
    head -22 "${BASH_SOURCE[0]}" | tail -18 | sed 's/^#//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -d|--days)
                VALIDITY_DAYS="$2"
                shift 2
                ;;
            -c|--cn)
                SERVER_CN="$2"
                shift 2
                ;;
            --san)
                SUBJECT_ALT_NAMES="$2"
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

check_openssl() {
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is not installed"
        exit 1
    fi
    log_info "OpenSSL version: $(openssl version)"
}

create_output_dir() {
    log_info "Creating output directory: ${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"
}

generate_ca() {
    log_info "Generating CA certificate..."
    
    # Generate CA private key
    openssl genrsa -out "${OUTPUT_DIR}/ca.key" 4096
    
    # Generate CA certificate
    openssl req -new -x509 \
        -days "${VALIDITY_DAYS}" \
        -key "${OUTPUT_DIR}/ca.key" \
        -out "${OUTPUT_DIR}/ca.crt" \
        -subj "/C=US/ST=State/L=City/O=Dogcatcher Org/OU=IT/CN=Dogcatcher CA"
    
    log_success "CA certificate generated"
    log_info "  CA Key: ${OUTPUT_DIR}/ca.key"
    log_info "  CA Cert: ${OUTPUT_DIR}/ca.crt"
}

generate_server_cert() {
    log_info "Generating server certificate for ${SERVER_CN}..."
    
    # Create SAN config
    local san_config="${OUTPUT_DIR}/server_san.cnf"
    
    # Build SAN list
    local san_list=""
    local i=1
    IFS=',' read -ra SAN_ARRAY <<< "${SUBJECT_ALT_NAMES}"
    for san in "${SAN_ARRAY[@]}"; do
        san_list="${san_list}DNS.${i} = ${san}\n"
        ((i++))
    done
    # Add IP for localhost
    san_list="${san_list}IP.1 = 127.0.0.1"
    
    cat > "${san_config}" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
C = US
ST = State
L = City
O = Dogcatcher Org
OU = API
CN = ${SERVER_CN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
$(echo -e "${san_list}")
EOF

    # Generate server private key
    openssl genrsa -out "${OUTPUT_DIR}/server.key" 2048
    
    # Generate server CSR
    openssl req -new \
        -key "${OUTPUT_DIR}/server.key" \
        -out "${OUTPUT_DIR}/server.csr" \
        -config "${san_config}"
    
    # Sign server certificate with CA
    openssl x509 -req \
        -days "${VALIDITY_DAYS}" \
        -in "${OUTPUT_DIR}/server.csr" \
        -CA "${OUTPUT_DIR}/ca.crt" \
        -CAkey "${OUTPUT_DIR}/ca.key" \
        -CAcreateserial \
        -out "${OUTPUT_DIR}/server.crt" \
        -extensions req_ext \
        -extfile "${san_config}"
    
    # Cleanup CSR and temp config
    rm -f "${OUTPUT_DIR}/server.csr" "${san_config}"
    
    log_success "Server certificate generated"
    log_info "  Server Key: ${OUTPUT_DIR}/server.key"
    log_info "  Server Cert: ${OUTPUT_DIR}/server.crt"
}

generate_client_cert() {
    local client_name="$1"
    local client_cn="$2"
    
    log_info "Generating client certificate for ${client_cn}..."
    
    # Generate client private key
    openssl genrsa -out "${OUTPUT_DIR}/${client_name}.key" 2048
    
    # Generate client CSR
    openssl req -new \
        -key "${OUTPUT_DIR}/${client_name}.key" \
        -out "${OUTPUT_DIR}/${client_name}.csr" \
        -subj "/C=US/ST=State/L=City/O=Dogcatcher Org/OU=Clients/CN=${client_cn}"
    
    # Sign client certificate with CA
    openssl x509 -req \
        -days "${VALIDITY_DAYS}" \
        -in "${OUTPUT_DIR}/${client_name}.csr" \
        -CA "${OUTPUT_DIR}/ca.crt" \
        -CAkey "${OUTPUT_DIR}/ca.key" \
        -CAcreateserial \
        -out "${OUTPUT_DIR}/${client_name}.crt"
    
    # Create combined PEM for some clients
    cat "${OUTPUT_DIR}/${client_name}.crt" "${OUTPUT_DIR}/${client_name}.key" > "${OUTPUT_DIR}/${client_name}.pem"
    
    # Cleanup CSR
    rm -f "${OUTPUT_DIR}/${client_name}.csr"
    
    log_success "Client certificate generated: ${client_name}"
    log_info "  Client Key: ${OUTPUT_DIR}/${client_name}.key"
    log_info "  Client Cert: ${OUTPUT_DIR}/${client_name}.crt"
    log_info "  Combined PEM: ${OUTPUT_DIR}/${client_name}.pem"
}

verify_certificates() {
    log_info "Verifying certificates..."
    
    # Verify server cert against CA
    if openssl verify -CAfile "${OUTPUT_DIR}/ca.crt" "${OUTPUT_DIR}/server.crt" > /dev/null 2>&1; then
        log_success "Server certificate verified against CA"
    else
        log_error "Server certificate verification failed"
        exit 1
    fi
    
    # Verify Kong client cert against CA
    if openssl verify -CAfile "${OUTPUT_DIR}/ca.crt" "${OUTPUT_DIR}/kong-client.crt" > /dev/null 2>&1; then
        log_success "Kong client certificate verified against CA"
    else
        log_error "Kong client certificate verification failed"
        exit 1
    fi
}

create_kubernetes_secrets_yaml() {
    log_info "Creating Kubernetes secrets YAML..."
    
    local secrets_file="${OUTPUT_DIR}/k8s-mtls-secrets.yaml"
    
    cat > "${secrets_file}" << EOF
# Kubernetes secrets for mTLS certificates
# Apply with: kubectl apply -f k8s-mtls-secrets.yaml

---
# CA Certificate (shared)
apiVersion: v1
kind: Secret
metadata:
  name: mtls-ca
  namespace: default
type: Opaque
data:
  ca.crt: $(base64 -i "${OUTPUT_DIR}/ca.crt" | tr -d '\n')

---
# Dogcatcher Server Certificate
apiVersion: v1
kind: Secret
metadata:
  name: dogcatcher-server-cert
  namespace: default
type: kubernetes.io/tls
data:
  tls.crt: $(base64 -i "${OUTPUT_DIR}/server.crt" | tr -d '\n')
  tls.key: $(base64 -i "${OUTPUT_DIR}/server.key" | tr -d '\n')
  ca.crt: $(base64 -i "${OUTPUT_DIR}/ca.crt" | tr -d '\n')

---
# Kong Client Certificate
apiVersion: v1
kind: Secret
metadata:
  name: kong-client-cert
  namespace: kong
type: kubernetes.io/tls
data:
  tls.crt: $(base64 -i "${OUTPUT_DIR}/kong-client.crt" | tr -d '\n')
  tls.key: $(base64 -i "${OUTPUT_DIR}/kong-client.key" | tr -d '\n')
  ca.crt: $(base64 -i "${OUTPUT_DIR}/ca.crt" | tr -d '\n')
EOF
    
    log_success "Kubernetes secrets YAML created: ${secrets_file}"
}

print_summary() {
    echo ""
    echo "=============================================="
    echo "  mTLS Certificates Generated Successfully"
    echo "=============================================="
    echo ""
    echo "Output directory: ${OUTPUT_DIR}"
    echo ""
    echo "Files created:"
    echo "  CA Certificate:"
    echo "    - ca.crt (CA certificate)"
    echo "    - ca.key (CA private key - keep secure!)"
    echo ""
    echo "  Server (Dogcatcher API):"
    echo "    - server.crt (server certificate)"
    echo "    - server.key (server private key)"
    echo ""
    echo "  Client (Kong Gateway):"
    echo "    - kong-client.crt (client certificate)"
    echo "    - kong-client.key (client private key)"
    echo "    - kong-client.pem (combined cert+key)"
    echo ""
    echo "  Kubernetes:"
    echo "    - k8s-mtls-secrets.yaml (ready to apply)"
    echo ""
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. For Docker Compose (local development):"
    echo "   Copy certs to app container and set environment:"
    echo "     MTLS_ENABLED=true"
    echo "     CERT_DIR=/app/certs"
    echo ""
    echo "2. For Kubernetes:"
    echo "   kubectl apply -f ${OUTPUT_DIR}/k8s-mtls-secrets.yaml"
    echo ""
    echo "3. Configure Kong to use client certificate"
    echo "   See: docs/KONG-MTLS-SETUP.md"
    echo ""
}

main() {
    parse_args "$@"
    
    echo ""
    log_info "mTLS Certificate Generation"
    log_info "  Output Dir: ${OUTPUT_DIR}"
    log_info "  Validity: ${VALIDITY_DAYS} days"
    log_info "  Server CN: ${SERVER_CN}"
    log_info "  SANs: ${SUBJECT_ALT_NAMES}"
    echo ""
    
    check_openssl
    create_output_dir
    generate_ca
    generate_server_cert
    generate_client_cert "kong-client" "kong-gateway"
    verify_certificates
    create_kubernetes_secrets_yaml
    print_summary
}

main "$@"
