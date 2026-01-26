#!/bin/bash

# Load Docker images into kind cluster
echo "Loading images into kind cluster..."

KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-kind}

# Load images
echo "Loading producer-app:latest..."
kind load docker-image producer-app:latest --name $KIND_CLUSTER_NAME

echo "Loading consumer-app:latest..."
kind load docker-image consumer-app:latest --name $KIND_CLUSTER_NAME

echo "✅ Images loaded into kind cluster successfully!"
