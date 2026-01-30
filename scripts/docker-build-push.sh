#!/bin/bash
#
# Build and push container images to Docker Hub
#
# Images are built for linux/amd64 (x86_64) architecture to ensure
# compatibility with standard Kubernetes clusters, even when building
# on Apple Silicon (ARM) Macs.
#
# Usage:
#   ./docker-build-push.sh [OPTIONS]
#
# Options:
#   -u, --username    Docker Hub username (required, or set DOCKER_USERNAME env var)
#   -t, --tag         Image tag (default: latest)
#   -a, --app         App to build: citizen, dogcatcher, or all (default: all)
#   -p, --push        Push to Docker Hub (default: build only)
#   -h, --help        Show this help message
#
# Examples:
#   ./docker-build-push.sh -u myuser -t v1.0.0 -p
#   ./docker-build-push.sh --username myuser --app citizen --push
#   DOCKER_USERNAME=myuser ./docker-build-push.sh -t latest -p
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
DOCKER_USERNAME="${DOCKER_USERNAME:-}"
IMAGE_TAG="latest"
APP_TO_BUILD="all"
PUSH_IMAGES=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Show help
show_help() {
    head -28 "${BASH_SOURCE[0]}" | tail -24 | sed 's/^#//'
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -u|--username)
                DOCKER_USERNAME="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -a|--app)
                APP_TO_BUILD="$2"
                shift 2
                ;;
            -p|--push)
                PUSH_IMAGES=true
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

# Validate inputs
validate_inputs() {
    if [[ -z "${DOCKER_USERNAME}" ]]; then
        log_error "Docker Hub username is required. Use -u/--username or set DOCKER_USERNAME env var."
        exit 1
    fi

    if [[ ! "${APP_TO_BUILD}" =~ ^(citizen|dogcatcher|all)$ ]]; then
        log_error "Invalid app: ${APP_TO_BUILD}. Must be 'citizen', 'dogcatcher', or 'all'."
        exit 1
    fi

    if [[ ! -d "${PROJECT_ROOT}/citizen-app" ]]; then
        log_error "citizen-app directory not found at ${PROJECT_ROOT}/citizen-app"
        exit 1
    fi

    if [[ ! -d "${PROJECT_ROOT}/app" ]]; then
        log_error "app (dogcatcher) directory not found at ${PROJECT_ROOT}/app"
        exit 1
    fi
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check for buildx support (required for cross-platform builds)
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is not available. Required for cross-platform builds."
        log_error "Please update Docker Desktop or install buildx plugin."
        exit 1
    fi

    log_info "Docker with buildx support is available"
}

# Check Docker Hub login
check_docker_login() {
    if [[ "${PUSH_IMAGES}" == true ]]; then
        log_info "Checking Docker Hub authentication..."
        if ! docker login --username "${DOCKER_USERNAME}" 2>/dev/null; then
            log_warn "Not logged in to Docker Hub. Please login:"
            docker login --username "${DOCKER_USERNAME}"
        fi
        log_success "Docker Hub authentication verified"
    fi
}

# Target platform for Kubernetes deployment (x86_64)
TARGET_PLATFORM="linux/amd64"

# Build an image
build_image() {
    local app_name="$1"
    local app_dir="$2"
    local image_name="${DOCKER_USERNAME}/${app_name}:${IMAGE_TAG}"

    log_info "Building ${image_name} for platform ${TARGET_PLATFORM}..."

    if docker buildx build \
        --platform "${TARGET_PLATFORM}" \
        --load \
        -t "${image_name}" \
        "${app_dir}"; then
        log_success "Built ${image_name}"
        
        # Also tag as latest if not already
        if [[ "${IMAGE_TAG}" != "latest" ]]; then
            local latest_tag="${DOCKER_USERNAME}/${app_name}:latest"
            docker tag "${image_name}" "${latest_tag}"
            log_info "Also tagged as ${latest_tag}"
        fi
    else
        log_error "Failed to build ${image_name}"
        return 1
    fi
}

# Push an image
push_image() {
    local app_name="$1"
    local image_name="${DOCKER_USERNAME}/${app_name}:${IMAGE_TAG}"

    log_info "Pushing ${image_name}..."

    if docker push "${image_name}"; then
        log_success "Pushed ${image_name}"
        
        # Also push latest if we tagged it
        if [[ "${IMAGE_TAG}" != "latest" ]]; then
            local latest_tag="${DOCKER_USERNAME}/${app_name}:latest"
            log_info "Pushing ${latest_tag}..."
            docker push "${latest_tag}"
            log_success "Pushed ${latest_tag}"
        fi
    else
        log_error "Failed to push ${image_name}"
        return 1
    fi
}

# Build and optionally push citizen app
build_citizen() {
    build_image "model-citizen" "${PROJECT_ROOT}/citizen-app"
    
    if [[ "${PUSH_IMAGES}" == true ]]; then
        push_image "model-citizen"
    fi
}

# Build and optionally push dogcatcher app
build_dogcatcher() {
    build_image "dogcatcher" "${PROJECT_ROOT}/app"
    
    if [[ "${PUSH_IMAGES}" == true ]]; then
        push_image "dogcatcher"
    fi
}

# Main function
main() {
    parse_args "$@"
    validate_inputs
    check_docker
    check_docker_login

    echo ""
    log_info "Build Configuration:"
    log_info "  Docker Username: ${DOCKER_USERNAME}"
    log_info "  Image Tag: ${IMAGE_TAG}"
    log_info "  App(s) to build: ${APP_TO_BUILD}"
    log_info "  Push to Docker Hub: ${PUSH_IMAGES}"
    echo ""

    case "${APP_TO_BUILD}" in
        citizen)
            build_citizen
            ;;
        dogcatcher)
            build_dogcatcher
            ;;
        all)
            build_citizen
            build_dogcatcher
            ;;
    esac

    echo ""
    log_success "Build complete!"
    echo ""
    log_info "Images created:"
    
    if [[ "${APP_TO_BUILD}" == "citizen" ]] || [[ "${APP_TO_BUILD}" == "all" ]]; then
        echo "  - ${DOCKER_USERNAME}/model-citizen:${IMAGE_TAG}"
    fi
    
    if [[ "${APP_TO_BUILD}" == "dogcatcher" ]] || [[ "${APP_TO_BUILD}" == "all" ]]; then
        echo "  - ${DOCKER_USERNAME}/dogcatcher:${IMAGE_TAG}"
    fi

    if [[ "${PUSH_IMAGES}" == false ]]; then
        echo ""
        log_info "To push images, run with -p/--push flag"
    fi
}

main "$@"
