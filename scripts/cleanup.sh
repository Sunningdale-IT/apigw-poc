#!/bin/bash

# Cleanup all deployed resources
echo "🧹 Cleaning up Kong API Gateway PoC..."

echo "Deleting Consumer resources..."
kubectl delete -f k8s-manifests/consumer/ --ignore-not-found=true

echo "Deleting Producer resources..."
kubectl delete -f k8s-manifests/producer/ --ignore-not-found=true

echo "Deleting Kong resources..."
kubectl delete -f k8s-manifests/kong/ --ignore-not-found=true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To verify, run: kubectl get namespaces | grep -E '(kong|producer|consumer)'"
