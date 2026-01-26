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
echo "  1. Tag images for your Azure Container Registry (ACR):"
echo "     docker tag producer-app:latest <your-acr>.azurecr.io/producer-app:latest"
echo "     docker tag consumer-app:latest <your-acr>.azurecr.io/consumer-app:latest"
echo "  2. Push images to ACR:"
echo "     docker push <your-acr>.azurecr.io/producer-app:latest"
echo "     docker push <your-acr>.azurecr.io/consumer-app:latest"
echo "  3. Update image references in k8s-manifests/*/01-deployment.yaml"
echo "  4. Deploy to AKS: Run './scripts/deploy.sh'"
