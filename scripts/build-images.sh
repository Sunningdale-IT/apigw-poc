#!/bin/bash

# Build Docker images for Producer and Consumer applications
echo "Building Docker images..."

# Build Producer image
echo "Building Producer application..."
docker build -t jimleitch/producer-app:latest ./producer-app

# Build Consumer image
echo "Building Consumer application..."
docker build -t jimleitch/consumer-app:latest ./consumer-app

echo "✅ Docker images built successfully!"
echo ""
echo "Images created:"
echo "  - jimleitch/producer-app:latest"
echo "  - jimleitch/consumer-app:latest"
echo ""
echo "Next steps:"
echo "  1. Push images to Docker Hub:"
echo "     docker push jimleitch/producer-app:latest"
echo "     docker push jimleitch/consumer-app:latest"
echo "  2. Deploy to AKS: Run './scripts/deploy.sh'"
echo ""
echo "Note: Make sure you are logged in to Docker Hub:"
echo "     docker login"
