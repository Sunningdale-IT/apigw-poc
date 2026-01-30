#!/bin/bash
#
# Setup Let's Encrypt certificates for Dogcatcher Proxy
#
# This script obtains and configures Let's Encrypt TLS certificates
# for the Dogcatcher API proxy.
#
# Prerequisites:
#   - Domain name pointing to your server
#   - Port 80 accessible from the internet
#   - Docker Compose running
#
# Usage:
#   ./setup-letsencrypt.sh [OPTIONS]
#
# Options:
#   -d, --domain      Domain name (required)
#   -e, --email       Email for Let's Encrypt notifications (required)
#   --staging         Use Let's Encrypt staging (for testing)
#   --dry-run         Test without obtaining certificate
#   -h, --help        Show this help message
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
DOMAIN=""
EMAIL=""
STAGING=false
DRY_RUN=false

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
    head -24 "${BASH_SOURCE[0]}" | tail -20 | sed 's/^#//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            --staging)
                STAGING=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
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

validate_inputs() {
    if [[ -z "${DOMAIN}" ]]; then
        log_error "Domain is required. Use -d or --domain"
        exit 1
    fi
    
    if [[ -z "${EMAIL}" ]]; then
        log_error "Email is required. Use -e or --email"
        exit 1
    fi
    
    # Validate email format
    if [[ ! "${EMAIL}" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        log_error "Invalid email format: ${EMAIL}"
        exit 1
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if proxy container is running
    if ! docker ps --format '{{.Names}}' | grep -q "dogcatcher-proxy"; then
        log_warn "dogcatcher-proxy container is not running"
        log_info "Starting containers..."
        cd "${PROJECT_ROOT}" && docker compose up -d proxy
        sleep 5
    fi
    
    log_success "Prerequisites check passed"
}

test_domain_accessibility() {
    log_info "Testing domain accessibility..."
    
    # Test if domain resolves
    if ! host "${DOMAIN}" > /dev/null 2>&1; then
        log_error "Domain ${DOMAIN} does not resolve. Check DNS configuration."
        exit 1
    fi
    
    # Test if port 80 is accessible
    log_info "Testing HTTP access to ${DOMAIN}..."
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://${DOMAIN}/health" 2>/dev/null || echo "000")
    
    if [[ "${http_code}" == "000" ]]; then
        log_warn "Could not connect to http://${DOMAIN}"
        log_warn "Ensure port 80 is open and domain points to this server"
    else
        log_success "Domain is accessible (HTTP ${http_code})"
    fi
}

obtain_certificate() {
    log_info "Obtaining Let's Encrypt certificate..."
    
    local certbot_args=(
        "certonly"
        "--webroot"
        "--webroot-path=/var/www/certbot"
        "--email" "${EMAIL}"
        "--agree-tos"
        "--no-eff-email"
        "-d" "${DOMAIN}"
    )
    
    if [[ "${STAGING}" == true ]]; then
        log_warn "Using Let's Encrypt STAGING environment"
        certbot_args+=("--staging")
    fi
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_warn "DRY RUN - not obtaining certificate"
        certbot_args+=("--dry-run")
    fi
    
    # Run certbot in the proxy container
    docker exec dogcatcher-proxy certbot "${certbot_args[@]}"
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_success "Dry run completed successfully"
    else
        log_success "Certificate obtained successfully"
    fi
}

configure_nginx() {
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "Skipping nginx configuration (dry run)"
        return
    fi
    
    log_info "Configuring nginx to use Let's Encrypt certificate..."
    
    # Create symlinks to Let's Encrypt certificates
    docker exec dogcatcher-proxy sh -c "
        ln -sf /etc/letsencrypt/live/${DOMAIN}/fullchain.pem /etc/nginx/certs/server.crt
        ln -sf /etc/letsencrypt/live/${DOMAIN}/privkey.pem /etc/nginx/certs/server.key
    "
    
    # Test nginx configuration
    docker exec dogcatcher-proxy nginx -t
    
    # Reload nginx
    docker exec dogcatcher-proxy nginx -s reload
    
    log_success "Nginx configured and reloaded"
}

setup_auto_renewal() {
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "Skipping auto-renewal setup (dry run)"
        return
    fi
    
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal script
    docker exec dogcatcher-proxy sh -c 'cat > /etc/periodic/daily/certbot-renew << "SCRIPT"
#!/bin/sh
certbot renew --quiet --deploy-hook "nginx -s reload"
SCRIPT
chmod +x /etc/periodic/daily/certbot-renew'
    
    log_success "Auto-renewal configured (daily check via crond)"
}

print_summary() {
    echo ""
    echo "=============================================="
    echo "  Let's Encrypt Setup Complete"
    echo "=============================================="
    echo ""
    echo "  Domain: ${DOMAIN}"
    echo "  Email: ${EMAIL}"
    if [[ "${STAGING}" == true ]]; then
        echo "  Environment: STAGING (not trusted by browsers)"
    else
        echo "  Environment: PRODUCTION"
    fi
    echo ""
    echo "  Certificate location (in container):"
    echo "    /etc/letsencrypt/live/${DOMAIN}/"
    echo ""
    echo "  Test HTTPS:"
    echo "    curl https://${DOMAIN}/health"
    echo ""
    echo "  Endpoints available:"
    echo "    https://${DOMAIN}/plain/dogs/"
    echo "    https://${DOMAIN}/apikey/dogs/"
    echo "    https://${DOMAIN}/mtls/dogs/"
    echo "    https://${DOMAIN}/jwt/dogs/"
    echo "    https://${DOMAIN}/oidc/dogs/"
    echo ""
    if [[ "${STAGING}" == true ]]; then
        echo "  NOTE: Staging certificates are not trusted!"
        echo "  Re-run without --staging for production certificates."
    fi
    echo "=============================================="
}

main() {
    parse_args "$@"
    validate_inputs
    
    echo ""
    log_info "Let's Encrypt Certificate Setup"
    log_info "  Domain: ${DOMAIN}"
    log_info "  Email: ${EMAIL}"
    log_info "  Staging: ${STAGING}"
    log_info "  Dry Run: ${DRY_RUN}"
    echo ""
    
    check_prerequisites
    test_domain_accessibility
    obtain_certificate
    configure_nginx
    setup_auto_renewal
    print_summary
}

main "$@"
