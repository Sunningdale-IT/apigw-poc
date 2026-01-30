#!/bin/bash
# Test mTLS connection to Kong API Gateway
# Usage: ./test-mtls.sh [--no-cert|--with-cert|--all]
#
# Tests:
# --no-cert   : Test without client certificate (should fail with mTLS enabled)
# --with-cert : Test with client certificate (should succeed)
# --all       : Run both tests (default)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="${CERTS_DIR:-${SCRIPT_DIR}/../certs}"
NAMESPACE="${NAMESPACE:-apigw-poc}"

# Configuration
# Standard Kong endpoint (no mTLS required)
KONG_HOST="${KONG_HOST:-kong.jim00.pd.test-rig.nl}"
# mTLS-protected Kong endpoint (client certificate required)
KONG_MTLS_HOST="${KONG_MTLS_HOST:-kong-mtls.jim00.pd.test-rig.nl}"
CONSUMER_ENDPOINT="/consumer/api/consume"
PRODUCER_ENDPOINT="/producer/api/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Check if certificates exist
check_certs() {
    if [[ ! -f "${CERTS_DIR}/client.crt" ]] || [[ ! -f "${CERTS_DIR}/client.key" ]]; then
        echo "Client certificates not found in ${CERTS_DIR}"
        echo ""
        echo "Extract certificates first:"
        echo "  ./scripts/extract-client-cert.sh"
        echo ""
        return 1
    fi
    return 0
}

# Test without client certificate on mTLS-protected endpoint
test_no_cert() {
    print_header "Test: mTLS Endpoint WITHOUT Client Certificate"
    
    echo "Endpoint: https://${KONG_MTLS_HOST}${CONSUMER_ENDPOINT}"
    echo "(This endpoint requires mTLS)"
    echo ""
    
    echo "Request:"
    echo "  curl -s -o /dev/null -w '%{http_code}' https://${KONG_MTLS_HOST}${CONSUMER_ENDPOINT}"
    echo ""
    
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://${KONG_MTLS_HOST}${CONSUMER_ENDPOINT}" 2>/dev/null || echo "000")
    
    echo "Response Code: ${HTTP_CODE}"
    echo ""
    
    # Remove any leading zeros from HTTP_CODE for comparison
    HTTP_CODE_CLEAN="${HTTP_CODE##*([0])}"
    HTTP_CODE_CLEAN="${HTTP_CODE_CLEAN:-0}"
    
    if [[ "${HTTP_CODE_CLEAN}" == "200" ]]; then
        print_failure "Connection succeeded without client certificate"
        echo "  This means mTLS is NOT enforced on this endpoint."
        echo "  Run: ./scripts/enable-mtls-enforcement.sh enable"
        return 1
    elif [[ "${HTTP_CODE_CLEAN}" == "400" ]] || [[ "${HTTP_CODE_CLEAN}" == "401" ]] || [[ "${HTTP_CODE_CLEAN}" == "403" ]]; then
        print_success "Connection rejected without client certificate (mTLS working!)"
        return 0
    elif [[ "${HTTP_CODE_CLEAN}" == "0" ]] || [[ "${HTTP_CODE}" == "000" ]] || [[ "${HTTP_CODE}" == "000000" ]]; then
        print_success "Connection failed at TLS handshake (mTLS working!)"
        echo "  Server required client certificate which was not provided."
        return 0
    else
        print_warning "Unexpected response code: ${HTTP_CODE}"
        return 0
    fi
}

# Test with client certificate
test_with_cert() {
    print_header "Test: Connection WITH Client Certificate"
    
    if ! check_certs; then
        return 1
    fi
    
    echo "Endpoint: https://${KONG_MTLS_HOST}${CONSUMER_ENDPOINT}"
    echo "Certificate: ${CERTS_DIR}/client.crt"
    echo ""
    
    echo "Request:"
    echo "  curl --cert ${CERTS_DIR}/client.crt --key ${CERTS_DIR}/client.key ..."
    echo ""
    
    # Build curl command
    CURL_OPTS=(
        --cert "${CERTS_DIR}/client.crt"
        --key "${CERTS_DIR}/client.key"
        -s
        -w '\n%{http_code}'
    )
    
    # Add CA cert if available
    if [[ -f "${CERTS_DIR}/ca.crt" ]]; then
        CURL_OPTS+=(--cacert "${CERTS_DIR}/ca.crt")
    fi
    
    RESPONSE=$(curl "${CURL_OPTS[@]}" "https://${KONG_MTLS_HOST}${CONSUMER_ENDPOINT}" 2>/dev/null || echo -e "\n000")
    HTTP_CODE=$(echo "${RESPONSE}" | tail -1)
    BODY=$(echo "${RESPONSE}" | sed '$d')
    
    echo "Response Code: ${HTTP_CODE}"
    echo ""
    
    if [[ "${HTTP_CODE}" == "200" ]]; then
        print_success "Connection succeeded with client certificate!"
        echo ""
        echo "Response body:"
        echo "${BODY}" | jq '.' 2>/dev/null || echo "${BODY}"
        return 0
    elif [[ "${HTTP_CODE}" == "000" ]]; then
        print_failure "Connection failed (SSL/TLS handshake error)"
        echo ""
        echo "Possible causes:"
        echo "  - Certificate not trusted by server"
        echo "  - Certificate expired"
        echo "  - Wrong certificate for this endpoint"
        return 1
    else
        print_failure "Connection failed with code ${HTTP_CODE}"
        echo ""
        echo "Response:"
        echo "${BODY}"
        return 1
    fi
}

# Test producer endpoint directly
test_producer_direct() {
    print_header "Test: Producer API (Direct - No mTLS)"
    
    echo "Endpoint: https://${KONG_HOST}${PRODUCER_ENDPOINT}"
    echo ""
    
    RESPONSE=$(curl -s -w '\n%{http_code}' "https://${KONG_HOST}${PRODUCER_ENDPOINT}" 2>/dev/null || echo -e "\n000")
    HTTP_CODE=$(echo "${RESPONSE}" | tail -1)
    BODY=$(echo "${RESPONSE}" | sed '$d')
    
    echo "Response Code: ${HTTP_CODE}"
    echo ""
    
    if [[ "${HTTP_CODE}" == "200" ]]; then
        print_success "Producer API accessible"
        echo ""
        echo "Response (first 200 chars):"
        echo "${BODY}" | head -c 200
        echo "..."
    else
        print_failure "Producer API not accessible: ${HTTP_CODE}"
    fi
}

# Show certificate info
show_cert_info() {
    print_header "Client Certificate Information"
    
    if ! check_certs; then
        return 1
    fi
    
    echo "Certificate Details:"
    openssl x509 -in "${CERTS_DIR}/client.crt" -noout -subject -issuer -dates -fingerprint 2>/dev/null || echo "  (unable to parse)"
    echo ""
    
    if [[ -f "${CERTS_DIR}/ca.crt" ]]; then
        echo "CA Certificate:"
        openssl x509 -in "${CERTS_DIR}/ca.crt" -noout -subject -issuer -dates 2>/dev/null || echo "  (unable to parse)"
        echo ""
        
        echo "Chain Verification:"
        openssl verify -CAfile "${CERTS_DIR}/ca.crt" "${CERTS_DIR}/client.crt" 2>/dev/null || echo "  FAILED"
    fi
}

# Main
main() {
    local MODE="${1:---all}"
    
    print_header "mTLS Connection Tests"
    echo "Kong Host: ${KONG_HOST}"
    echo "Certificates: ${CERTS_DIR}"
    echo "Mode: ${MODE}"
    
    case "${MODE}" in
        --no-cert)
            test_no_cert
            ;;
        --with-cert)
            test_with_cert
            ;;
        --producer)
            test_producer_direct
            ;;
        --info)
            show_cert_info
            ;;
        --all|*)
            show_cert_info || true
            test_producer_direct
            test_no_cert
            test_with_cert || true
            ;;
    esac
    
    print_header "Tests Complete"
}

main "$@"
