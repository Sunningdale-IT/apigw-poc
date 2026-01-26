#!/bin/bash

# Check the status of all components
echo "📊 Kong API Gateway PoC - Status Check"
echo "======================================"
echo ""

echo "🔹 Kong Namespace:"
kubectl get all -n kong
echo ""

echo "🔹 Producer Namespace:"
kubectl get all -n producer
echo ""

echo "🔹 Consumer Namespace:"
kubectl get all -n consumer
echo ""

echo "📋 Pod Logs (last 10 lines):"
echo "----------------------------"
echo ""

echo "Kong logs:"
kubectl logs -n kong -l app=kong-proxy --tail=10
echo ""

echo "Producer logs:"
kubectl logs -n producer -l app=producer --tail=10
echo ""

echo "Consumer logs:"
kubectl logs -n consumer -l app=consumer --tail=10
echo ""
