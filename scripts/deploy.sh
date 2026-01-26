#!/bin/bash

# Deploy all components to Kubernetes
echo "🚀 Deploying Kong API Gateway PoC to Kubernetes..."
echo ""

# Deploy Kong namespace and components
echo "📦 Deploying Kong API Gateway..."
kubectl apply -f k8s-manifests/kong/00-namespace.yaml
kubectl apply -f k8s-manifests/kong/01-configmap.yaml
kubectl apply -f k8s-manifests/kong/02-deployment.yaml
kubectl apply -f k8s-manifests/kong/03-service.yaml

# Wait for Kong to be ready
echo "⏳ Waiting for Kong to be ready..."
kubectl wait --for=condition=ready pod -l app=kong-proxy -n kong --timeout=120s

echo ""
echo "📦 Deploying Producer application..."
kubectl apply -f k8s-manifests/producer/00-namespace.yaml
kubectl apply -f k8s-manifests/producer/01-deployment.yaml
kubectl apply -f k8s-manifests/producer/02-service.yaml

# Wait for Producer to be ready
echo "⏳ Waiting for Producer to be ready..."
kubectl wait --for=condition=ready pod -l app=producer -n producer --timeout=120s

echo ""
echo "📦 Deploying Consumer application..."
kubectl apply -f k8s-manifests/consumer/00-namespace.yaml
kubectl apply -f k8s-manifests/consumer/01-deployment.yaml
kubectl apply -f k8s-manifests/consumer/02-service.yaml

# Wait for Consumer to be ready
echo "⏳ Waiting for Consumer to be ready..."
kubectl wait --for=condition=ready pod -l app=consumer -n consumer --timeout=120s

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Status:"
echo "-------------------"
kubectl get pods -n kong
kubectl get pods -n producer
kubectl get pods -n consumer
echo ""
echo "🌐 Services:"
echo "-----------"
kubectl get svc -n kong
kubectl get svc -n producer
kubectl get svc -n consumer
echo ""
echo "📝 Next steps:"
echo "  Run './scripts/test-api.sh' to test the setup"
echo "  Run './scripts/status.sh' to check the status"
