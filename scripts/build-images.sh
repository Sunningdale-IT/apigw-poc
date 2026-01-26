#!/bin/bash

# Build Docker images for Producer and Consumer applications
echo "Building Docker images..."

# Build Producer image
echo "Building Producer application..."
docker build -t producer-app:latest ./producer-app

# Build Consumer image
echo "Building Consumer application..."
docker build -t consumer-app:latest ./consumer-app

echo "✅ Docker images built successfully!"
echo ""
echo "Images created:"
echo "  - producer-app:latest"
echo "  - consumer-app:latest"
echo ""
echo "Next steps:"
echo "  1. If using Minikube: Run 'eval \$(minikube docker-env)' before building"
echo "  2. If using kind: Run './scripts/load-images-kind.sh' to load images into kind cluster"
echo "  3. Deploy to Kubernetes: Run './scripts/deploy.sh'"
