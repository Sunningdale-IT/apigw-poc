#!/usr/bin/env bash
#
# Configure Kong API Gateway with multiple authentication routes
#
# This script sets up:
#   - /public/* - No authentication required (routes to /api/*)
#   - /apikey/* - Kong API Key authentication (routes to /api/*)
#   - /api/*    - Direct access (backend handles auth)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
KONG_ADMIN_URL="${KONG_ADMIN_URL:-http://localhost:8001}"
DOGCATCHER_HOST="${DOGCATCHER_HOST:-web}"
DOGCATCHER_PORT="${DOGCATCHER_PORT:-5000}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Wait for Kong to be ready
wait_for_kong() {
    log_info "Waiting for Kong Admin API..."
    local max_attempts=30
    local attempt=0
    
    while [[ ${attempt} -lt ${max_attempts} ]]; do
        if curl -s "${KONG_ADMIN_URL}/status" > /dev/null 2>&1; then
            log_success "Kong is ready"
            return 0
        fi
        ((attempt++))
        sleep 2
    done
    
    log_error "Kong is not responding after ${max_attempts} attempts"
    return 1
}

main() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}        ${GREEN}Kong API Gateway Configuration${NC}                      ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    wait_for_kong
    
    echo ""
    log_info "Configuring services and routes..."
    echo ""
    
    # Clean up existing configuration
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/public-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/apikey-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/api-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-public" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-apikey" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-direct" 2>/dev/null || true
    
    # ============================================
    # Public Route - No authentication
    # Routes /public/* to backend /api/*
    # ============================================
    log_info "Creating public service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-public" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}/api" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-public/routes" \
        -d "name=public-route" \
        -d "paths[]=/public" \
        -d "strip_path=true" > /dev/null
    
    # Add request-transformer to set X-Auth headers
    curl -s -X POST "${KONG_ADMIN_URL}/routes/public-route/plugins" \
        -d "name=request-transformer" \
        -d "config.add.headers=X-Auth-Mode:public" \
        -d "config.add.headers=X-Auth-Verified:true" > /dev/null
    
    log_success "Public route configured (/public/* -> /api/*)"
    
    # ============================================
    # API Key Route - Kong handles key auth
    # Routes /apikey/* to backend /api/*
    # ============================================
    log_info "Creating apikey service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-apikey" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}/api" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-apikey/routes" \
        -d "name=apikey-route" \
        -d "paths[]=/apikey" \
        -d "strip_path=true" > /dev/null
    
    # Add key-auth plugin
    curl -s -X POST "${KONG_ADMIN_URL}/routes/apikey-route/plugins" \
        -d "name=key-auth" \
        -d "config.key_names=X-API-Key" \
        -d "config.key_in_header=true" > /dev/null
    
    # Add request-transformer to set auth headers
    curl -s -X POST "${KONG_ADMIN_URL}/routes/apikey-route/plugins" \
        -d "name=request-transformer" \
        -d "config.add.headers=X-Auth-Mode:apikey" \
        -d "config.add.headers=X-Auth-Verified:true" > /dev/null
    
    log_success "API Key route configured (/apikey/* -> /api/*)"
    
    # ============================================
    # Direct API Route - Backend handles auth
    # Routes /api/* directly to backend /api/*
    # ============================================
    log_info "Creating direct API service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-direct" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-direct/routes" \
        -d "name=api-route" \
        -d "paths[]=/api" \
        -d "strip_path=false" > /dev/null
    
    log_success "Direct API route configured (/api/* -> /api/*)"
    
    # ============================================
    # Create API Key consumers
    # ============================================
    echo ""
    log_info "Creating API consumers..."
    
    # Check if consumer exists, create if not
    if ! curl -s "${KONG_ADMIN_URL}/consumers/model-citizen" | grep -q '"id"'; then
        curl -s -X POST "${KONG_ADMIN_URL}/consumers" \
            -d "username=model-citizen" > /dev/null
        log_info "Created consumer: model-citizen"
    else
        log_info "Consumer already exists: model-citizen"
    fi
    
    # Add API key if not exists
    if ! curl -s "${KONG_ADMIN_URL}/consumers/model-citizen/key-auth" | grep -q "citizen-api-key-2026"; then
        curl -s -X POST "${KONG_ADMIN_URL}/consumers/model-citizen/key-auth" \
            -d "key=citizen-api-key-2026" > /dev/null
        log_success "Added API key for model-citizen"
    else
        log_info "API key already exists for model-citizen"
    fi
    
    # Admin consumer
    if ! curl -s "${KONG_ADMIN_URL}/consumers/admin" | grep -q '"id"'; then
        curl -s -X POST "${KONG_ADMIN_URL}/consumers" \
            -d "username=admin" > /dev/null
        log_info "Created consumer: admin"
    fi
    
    if ! curl -s "${KONG_ADMIN_URL}/consumers/admin/key-auth" | grep -q "admin-api-key-2026"; then
        curl -s -X POST "${KONG_ADMIN_URL}/consumers/admin/key-auth" \
            -d "key=admin-api-key-2026" > /dev/null
        log_success "Added API key for admin"
    fi
    
    # ============================================
    # Summary
    # ============================================
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    log_success "Kong configuration complete!"
    echo ""
    echo "Available routes:"
    echo ""
    echo -e "  ${GREEN}/public/*${NC}  - No authentication required"
    echo "               Example: curl http://localhost:8000/public/dogs/"
    echo ""
    echo -e "  ${GREEN}/apikey/*${NC}  - Kong API Key authentication"
    echo "               Example: curl -H 'X-API-Key: citizen-api-key-2026' http://localhost:8000/apikey/dogs/"
    echo ""
    echo -e "  ${GREEN}/api/*${NC}     - Direct access (backend handles auth)"
    echo "               Example: curl -H 'X-API-Key: <backend-key>' http://localhost:8000/api/dogs/"
    echo ""
    echo "API Keys configured:"
    echo "  - citizen-api-key-2026 (for Model Citizen app)"
    echo "  - admin-api-key-2026 (for admin access)"
    echo ""
    echo "Kong Admin API: ${KONG_ADMIN_URL}"
    echo ""
}

main "$@"
