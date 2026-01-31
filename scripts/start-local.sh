#!/usr/bin/env bash
#
# Start local development environment and display access URLs
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

cd "${PROJECT_DIR}"

# Parse arguments
BUILD=""
DETACH="-d"
FOLLOW_LOGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            BUILD="--build"
            shift
            ;;
        --logs|-l)
            FOLLOW_LOGS="true"
            shift
            ;;
        --foreground|-f)
            DETACH=""
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --build       Rebuild containers before starting"
            echo "  -l, --logs        Follow logs after starting"
            echo "  -f, --foreground  Run in foreground (not detached)"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for .env file
if [[ ! -f "${PROJECT_DIR}/.env" ]]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [[ -f "${PROJECT_DIR}/.env.example" ]]; then
        cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
        echo -e "${GREEN}Created .env file from template${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}${BOLD}Starting Dogcatcher Development Environment...${NC}"
echo ""

# Start services
if [[ -n "${BUILD}" ]]; then
    echo -e "${CYAN}Building and starting containers...${NC}"
else
    echo -e "${CYAN}Starting containers...${NC}"
fi

# shellcheck disable=SC2086
docker compose up ${DETACH} ${BUILD}

# If running in foreground, don't show URLs (they'll be shown before logs take over)
if [[ -z "${DETACH}" ]]; then
    exit 0
fi

# Wait for services to be healthy
echo ""
echo -e "${CYAN}Waiting for services to be ready...${NC}"

MAX_WAIT=60
WAITED=0
while [[ ${WAITED} -lt ${MAX_WAIT} ]]; do
    # Check if web container is running
    if docker compose ps --status running 2>/dev/null | grep -q "dogcatcher-web"; then
        # Try to connect to the API
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/docs/ 2>/dev/null | grep -q "200"; then
            break
        fi
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done
echo ""

if [[ ${WAITED} -ge ${MAX_WAIT} ]]; then
    echo -e "${YELLOW}Warning: Services may not be fully ready yet${NC}"
fi

# Create default admin user if it doesn't exist
echo -e "${CYAN}Checking admin user...${NC}"
docker exec dogcatcher-web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Created default admin user')
else:
    print('Admin user already exists')
" 2>/dev/null || echo -e "${YELLOW}Could not create admin user (database may not be ready)${NC}"

# Configure Kong API Gateway
echo -e "${CYAN}Configuring Kong API Gateway...${NC}"
if docker ps | grep -q kong; then
    "${SCRIPT_DIR}/configure-kong.sh" 2>/dev/null || echo -e "${YELLOW}Kong configuration skipped (may already be configured)${NC}"
else
    echo -e "${YELLOW}Kong not running, skipping configuration${NC}"
fi

# Display access URLs
echo ""
echo -e "${GREEN}${BOLD}=============================================${NC}"
echo -e "${GREEN}${BOLD}   Dogcatcher Development Environment${NC}"
echo -e "${GREEN}${BOLD}=============================================${NC}"
echo ""
echo -e "${BOLD}Dogcatcher API (Direct):${NC}"
echo -e "  Web UI:      ${CYAN}http://localhost:5001/${NC}"
echo -e "  Swagger API: ${CYAN}http://localhost:5001/api/docs/${NC}"
echo -e "  Admin:       ${CYAN}http://localhost:5001/admin/${NC}  (user: admin, pass: admin123)"
echo ""
echo -e "${BOLD}Model Citizen App:${NC}"
echo -e "  Web UI:      ${CYAN}http://localhost:5002/${NC}"
echo -e "  Login:       ${CYAN}http://localhost:5002/login/${NC}  (use: DEMO)"
echo ""
echo -e "${BOLD}Kong API Gateway (port 8000):${NC}"
echo -e "  Public:      ${CYAN}http://localhost:8000/public/dogs/${NC}  (no auth)"
echo -e "  API Key:     ${CYAN}http://localhost:8000/apikey/dogs/${NC}  (X-API-Key header)"
echo -e "  Direct:      ${CYAN}http://localhost:8000/api/dogs/${NC}     (backend auth)"
echo -e "  Admin API:   ${CYAN}http://localhost:8001/${NC}"
echo ""
echo -e "${BOLD}Kong Manager OSS:${NC}"
echo -e "  URL:         ${CYAN}http://localhost:8002/${NC}  (no login required)"
echo ""
echo -e "${BOLD}Nginx Proxy (port 8080):${NC}"
echo -e "  HTTP:        ${CYAN}http://localhost:8080/${NC}"
echo -e "  HTTPS:       ${CYAN}https://localhost:8443/${NC}"
echo ""
echo -e "${BOLD}Database:${NC}"
echo -e "  PostgreSQL:  ${CYAN}localhost:5432${NC} (user: dogcatcher)"
echo ""
echo -e "${GREEN}${BOLD}=============================================${NC}"
echo ""
echo -e "${BOLD}Useful commands:${NC}"
echo -e "  View logs:           ${YELLOW}docker compose logs -f${NC}"
echo -e "  Stop services:       ${YELLOW}docker compose down${NC}"
echo -e "  Rebuild:             ${YELLOW}docker compose up -d --build${NC}"
echo -e "  Configure Kong:      ${YELLOW}./scripts/configure-kong.sh${NC}"
echo -e "  Load test data:      ${YELLOW}./scripts/load-test-data.sh${NC}"
echo ""

# Follow logs if requested
if [[ -n "${FOLLOW_LOGS}" ]]; then
    echo -e "${CYAN}Following logs (Ctrl+C to stop)...${NC}"
    echo ""
    docker compose logs -f
fi
