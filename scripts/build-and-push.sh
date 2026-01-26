#!/bin/bash

# Build and push Docker images to Docker Hub
# Container registry: https://hub.docker.com/repository/docker/jimleitch

set -e

echo "🔨 Building and pushing Docker images to jimleitch Docker Hub registry..."
echo ""

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Warning: You may not be logged in to Docker Hub."
    echo "Please run: docker login"
    echo ""
fi

# Build Producer image
echo "📦 Building Producer application..."
docker build -t jimleitch/producer-app:latest ./producer-app

# Build Consumer image
echo "📦 Building Consumer application..."
docker build -t jimleitch/consumer-app:latest ./consumer-app

echo ""
echo "🚀 Pushing images to Docker Hub..."

# Push Producer image
echo "  Pushing jimleitch/producer-app:latest..."
docker push jimleitch/producer-app:latest

# Push Consumer image
echo "  Pushing jimleitch/consumer-app:latest..."
docker push jimleitch/consumer-app:latest

echo ""
echo "✅ Images successfully built and pushed to Docker Hub!"
echo ""
echo "Images available at:"
echo "  - https://hub.docker.com/r/jimleitch/producer-app"
echo "  - https://hub.docker.com/r/jimleitch/consumer-app"
echo ""
echo "Next step: Deploy to Kubernetes"
echo "  ./scripts/deploy.sh"
