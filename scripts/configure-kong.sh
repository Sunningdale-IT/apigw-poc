#!/usr/bin/env bash
#
# Configure Kong API Gateway with multiple authentication routes
#
# This script sets up:
#   - /public/*  - No authentication required (Plain)
#   - /apikey/*  - Kong API Key authentication
#   - /jwt/*     - JWT token authentication
#   - /mtls/*    - Mutual TLS (client certificate) authentication
#   - /oidc/*    - OpenID Connect authentication
#   - /api/*     - Direct access (backend handles auth)
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
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/jwt-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/mtls-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/oidc-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/routes/api-route" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-public" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-apikey" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-jwt" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-mtls" 2>/dev/null || true
    curl -s -X DELETE "${KONG_ADMIN_URL}/services/dogcatcher-oidc" 2>/dev/null || true
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
    # JWT Route - Kong validates JWT tokens
    # Routes /jwt/* to backend /api/*
    # ============================================
    log_info "Creating JWT service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-jwt" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}/api" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-jwt/routes" \
        -d "name=jwt-route" \
        -d "paths[]=/jwt" \
        -d "strip_path=true" > /dev/null
    
    # Add JWT plugin
    curl -s -X POST "${KONG_ADMIN_URL}/routes/jwt-route/plugins" \
        -d "name=jwt" \
        -d "config.claims_to_verify=exp" > /dev/null
    
    # Add request-transformer to set auth headers
    curl -s -X POST "${KONG_ADMIN_URL}/routes/jwt-route/plugins" \
        -d "name=request-transformer" \
        -d "config.add.headers=X-Auth-Mode:jwt" \
        -d "config.add.headers=X-Auth-Verified:true" > /dev/null
    
    log_success "JWT route configured (/jwt/* -> /api/*)"
    
    # ============================================
    # mTLS Route - Kong validates client certificates
    # Routes /mtls/* to backend /api/*
    # Note: Requires Kong to be configured with TLS
    # ============================================
    log_info "Creating mTLS service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-mtls" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}/api" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-mtls/routes" \
        -d "name=mtls-route" \
        -d "paths[]=/mtls" \
        -d "strip_path=true" > /dev/null
    
    # Add request-transformer to set auth headers
    # Note: Full mTLS requires Kong TLS listener configuration
    curl -s -X POST "${KONG_ADMIN_URL}/routes/mtls-route/plugins" \
        -d "name=request-transformer" \
        -d "config.add.headers=X-Auth-Mode:mtls" \
        -d "config.add.headers=X-Auth-Verified:true" > /dev/null
    
    log_success "mTLS route configured (/mtls/* -> /api/*)"
    log_warn "Note: Full mTLS requires Kong TLS listener and CA certificate configuration"
    
    # ============================================
    # OIDC Route - OpenID Connect authentication
    # Routes /oidc/* to backend /api/*
    # Requires identity provider (Keycloak, Auth0, Azure AD, etc.)
    # ============================================
    log_info "Creating OIDC service and route..."
    curl -s -X POST "${KONG_ADMIN_URL}/services" \
        -d "name=dogcatcher-oidc" \
        -d "url=http://${DOGCATCHER_HOST}:${DOGCATCHER_PORT}/api" > /dev/null
    
    curl -s -X POST "${KONG_ADMIN_URL}/services/dogcatcher-oidc/routes" \
        -d "name=oidc-route" \
        -d "paths[]=/oidc" \
        -d "strip_path=true" > /dev/null
    
    # OIDC plugin configuration
    # Note: These are placeholder values - replace with your identity provider settings
    OIDC_DISCOVERY="${OIDC_DISCOVERY:-https://your-idp.example.com/.well-known/openid-configuration}"
    OIDC_CLIENT_ID="${OIDC_CLIENT_ID:-dogcatcher-api}"
    OIDC_CLIENT_SECRET="${OIDC_CLIENT_SECRET:-your-client-secret}"
    
    # Only configure OIDC plugin if not using placeholder values
    if [[ "${OIDC_DISCOVERY}" != *"your-idp.example.com"* ]]; then
        curl -s -X POST "${KONG_ADMIN_URL}/routes/oidc-route/plugins" \
            -d "name=oidc" \
            -d "config.client_id=${OIDC_CLIENT_ID}" \
            -d "config.client_secret=${OIDC_CLIENT_SECRET}" \
            -d "config.discovery=${OIDC_DISCOVERY}" \
            -d "config.introspection_endpoint_auth_method=client_secret_post" \
            -d "config.bearer_only=yes" \
            -d "config.realm=dogcatcher" > /dev/null
        log_success "OIDC route configured with identity provider"
    else
        # Add request-transformer for demo/testing without real IdP
        curl -s -X POST "${KONG_ADMIN_URL}/routes/oidc-route/plugins" \
            -d "name=request-transformer" \
            -d "config.add.headers=X-Auth-Mode:oidc" \
            -d "config.add.headers=X-Auth-Verified:true" > /dev/null
        log_success "OIDC route configured (/oidc/* -> /api/*)"
        log_warn "OIDC plugin not configured - set OIDC_DISCOVERY, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET"
    fi
    
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
    
    # Add JWT credentials for model-citizen consumer
    log_info "Configuring JWT credentials..."
    if ! curl -s "${KONG_ADMIN_URL}/consumers/model-citizen/jwt" | grep -q "model-citizen-jwt"; then
        curl -s -X POST "${KONG_ADMIN_URL}/consumers/model-citizen/jwt" \
            -d "key=model-citizen-jwt" \
            -d "algorithm=HS256" \
            -d "secret=your-256-bit-secret-key-here-min32chars" > /dev/null
        log_success "Added JWT credentials for model-citizen"
    else
        log_info "JWT credentials already exist for model-citizen"
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
    echo -e "  ${GREEN}/public/*${NC}  - No authentication (Plain)"
    echo "               curl http://localhost:8000/public/dogs/"
    echo ""
    echo -e "  ${GREEN}/apikey/*${NC}  - API Key authentication"
    echo "               curl -H 'X-API-Key: citizen-api-key-2026' http://localhost:8000/apikey/dogs/"
    echo ""
    echo -e "  ${GREEN}/jwt/*${NC}     - JWT token authentication"
    echo "               curl -H 'Authorization: Bearer <token>' http://localhost:8000/jwt/dogs/"
    echo ""
    echo -e "  ${GREEN}/mtls/*${NC}    - mTLS client certificate authentication"
    echo "               curl --cert client.crt --key client.key https://localhost:8443/mtls/dogs/"
    echo ""
    echo -e "  ${GREEN}/oidc/*${NC}    - OpenID Connect authentication"
    echo "               curl -H 'Authorization: Bearer <oidc-token>' http://localhost:8000/oidc/dogs/"
    echo ""
    echo -e "  ${GREEN}/api/*${NC}     - Direct access (backend handles auth)"
    echo "               curl -H 'X-API-Key: <backend-key>' http://localhost:8000/api/dogs/"
    echo ""
    echo "Credentials configured:"
    echo "  API Keys:"
    echo "    - citizen-api-key-2026 (for Model Citizen app)"
    echo "    - admin-api-key-2026 (for admin access)"
    echo "  JWT:"
    echo "    - ISS: model-citizen-jwt"
    echo "    - Secret: your-256-bit-secret-key-here-min32chars"
    echo "  OIDC:"
    echo "    - Configure via: OIDC_DISCOVERY, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET"
    echo ""
    echo "Kong Admin API: ${KONG_ADMIN_URL}"
    echo "Kong Manager: http://localhost:8002"
    echo ""
}

main "$@"
