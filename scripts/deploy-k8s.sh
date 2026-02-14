#!/bin/bash
set -e

# API Gateway POC Demo Suite - Quick Deploy Script
# This script helps you deploy the demo suite to Kubernetes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HELM_CHART_DIR="$REPO_ROOT/helm-chart/apigw-demo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  API Gateway POC Demo Suite - Kubernetes Quick Deploy        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}✗ kubectl not found. Please install kubectl.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ kubectl found${NC}"
    
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}✗ helm not found. Please install helm.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ helm found${NC}"
    
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}✗ Cannot connect to Kubernetes cluster. Check your kubeconfig.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
    echo ""
}

# Build Docker images
build_images() {
    echo -e "${YELLOW}Do you want to build Docker images? (y/n)${NC}"
    read -r BUILD_IMAGES
    
    if [[ "$BUILD_IMAGES" != "y" ]]; then
        echo "Skipping image build..."
        return
    fi
    
    echo -e "${YELLOW}Enter your container registry URL (default: docker.io/jimleitch):${NC}"
    read -r REGISTRY
    REGISTRY=${REGISTRY:-docker.io/jimleitch}
    
    echo -e "${YELLOW}Enter image tag (default: latest):${NC}"
    read -r TAG
    TAG=${TAG:-latest}
    
    echo ""
    echo -e "${BLUE}Building images for linux/amd64...${NC}"
    
    docker build --platform linux/amd64 -t "$REGISTRY/dogcatcher-api:$TAG" "$REPO_ROOT/app" || exit 1
    docker build --platform linux/amd64 -t "$REGISTRY/kong-oidc:$TAG" "$REPO_ROOT/kong" || exit 1
    docker build --platform linux/amd64 -t "$REGISTRY/model-citizen:$TAG" "$REPO_ROOT/citizen-app" || exit 1
    docker build --platform linux/amd64 -t "$REGISTRY/certosaurus:$TAG" "$REPO_ROOT/certosaurus" || exit 1
    
    echo ""
    echo -e "${YELLOW}Do you want to push images to registry? (y/n)${NC}"
    read -r PUSH_IMAGES
    
    if [[ "$PUSH_IMAGES" == "y" ]]; then
        echo -e "${BLUE}Pushing images...${NC}"
        docker push "$REGISTRY/dogcatcher-api:$TAG" || exit 1
        docker push "$REGISTRY/kong-oidc:$TAG" || exit 1
        docker push "$REGISTRY/model-citizen:$TAG" || exit 1
        docker push "$REGISTRY/certosaurus:$TAG" || exit 1
        echo -e "${GREEN}✓ Images pushed successfully${NC}"
    fi
    echo ""
}

# Create values file
create_values_file() {
    echo -e "${YELLOW}Creating custom values file...${NC}"
    
    if [[ -f "$HELM_CHART_DIR/my-values.yaml" ]]; then
        echo -e "${YELLOW}my-values.yaml already exists. Use existing file? (y/n)${NC}"
        read -r USE_EXISTING
        if [[ "$USE_EXISTING" == "y" ]]; then
            return
        fi
    fi
    
    cp "$HELM_CHART_DIR/values-example.yaml" "$HELM_CHART_DIR/my-values.yaml"
    
    echo ""
    echo -e "${YELLOW}Please edit $HELM_CHART_DIR/my-values.yaml before deploying.${NC}"
    echo -e "${YELLOW}Update the following:${NC}"
    echo "  - Image repositories (registry URLs)"
    echo "  - Image tags"
    echo "  - Secret keys and passwords"
    echo "  - Hostnames (if different from jim00.pd.test-rig.nl)"
    echo ""
    echo -e "${YELLOW}Press ENTER when you're ready to continue...${NC}"
    read -r
}

# Deploy with Helm
deploy() {
    echo -e "${YELLOW}Enter namespace (default: apigw-demo):${NC}"
    read -r NAMESPACE
    NAMESPACE=${NAMESPACE:-apigw-demo}
    
    echo -e "${YELLOW}Enter release name (default: apigw-demo):${NC}"
    read -r RELEASE_NAME
    RELEASE_NAME=${RELEASE_NAME:-apigw-demo}
    
    echo ""
    echo -e "${BLUE}Deploying with Helm...${NC}"
    
    # Check if release exists
    if helm status "$RELEASE_NAME" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${YELLOW}Release $RELEASE_NAME already exists. Upgrade? (y/n)${NC}"
        read -r UPGRADE
        if [[ "$UPGRADE" == "y" ]]; then
            helm upgrade "$RELEASE_NAME" "$HELM_CHART_DIR" \
                -f "$HELM_CHART_DIR/my-values.yaml" \
                -n "$NAMESPACE" || exit 1
            echo -e "${GREEN}✓ Upgrade completed${NC}"
        fi
    else
        helm install "$RELEASE_NAME" "$HELM_CHART_DIR" \
            -f "$HELM_CHART_DIR/my-values.yaml" \
            -n "$NAMESPACE" \
            --create-namespace || exit 1
        echo -e "${GREEN}✓ Installation completed${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Waiting for pods to be ready...${NC}"
    echo -e "${YELLOW}You can watch the status with: kubectl get pods -n $NAMESPACE -w${NC}"
    echo ""
}

# Show next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Deployment Complete!                                        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Check deployment status:"
    echo "   kubectl get pods -n $NAMESPACE"
    echo ""
    echo "2. Wait for certificates:"
    echo "   kubectl get certificates -n $NAMESPACE"
    echo ""
    echo "3. View deployment info:"
    echo "   helm status $RELEASE_NAME -n $NAMESPACE"
    echo ""
    echo "4. Access the applications (after certificates are ready):"
    echo "   - Dogcatcher: https://dogcatcher.jim00.pd.test-rig.nl/admin/"
    echo "   - Kong Proxy: https://kong.jim00.pd.test-rig.nl/"
    echo "   - Kong Manager: https://kong-manager.jim00.pd.test-rig.nl/"
    echo "   - Model Citizen: https://citizen.jim00.pd.test-rig.nl/"
    echo "   - Certosaurus: https://certosaurus.jim00.pd.test-rig.nl/login/"
    echo "   - Keycloak: https://keycloak.jim00.pd.test-rig.nl/"
    echo ""
    echo -e "${YELLOW}For detailed instructions, see: $HELM_CHART_DIR/DEPLOYMENT.md${NC}"
    echo ""
}

# Main flow
main() {
    check_prerequisites
    build_images
    create_values_file
    deploy
    show_next_steps
}

main
