#!/bin/bash

# Test the Kong API Gateway setup
echo "🧪 Testing Kong API Gateway PoC..."
echo ""

# Detect Kubernetes environment
if kubectl cluster-info | grep -q "kind"; then
    KONG_HOST="localhost"
    KONG_PORT="30080"
    echo "Detected kind cluster - using localhost:30080"
elif kubectl cluster-info | grep -q "minikube"; then
    KONG_HOST=$(minikube ip)
    KONG_PORT="30080"
    echo "Detected Minikube cluster - using $(minikube ip):30080"
else
    KONG_HOST="localhost"
    KONG_PORT="30080"
    echo "Using localhost:30080 (adjust if needed for your cluster)"
fi

KONG_URL="http://${KONG_HOST}:${KONG_PORT}"

echo ""
echo "🔍 Testing Kong Admin API..."
curl -s http://${KONG_HOST}:30081/status | jq '.' 2>/dev/null || echo "Kong admin API accessible"

echo ""
echo "🔍 Testing Producer service via Kong..."
echo "GET ${KONG_URL}/producer/health"
curl -s ${KONG_URL}/producer/health | jq '.' || curl -s ${KONG_URL}/producer/health
echo ""

echo ""
echo "📊 Getting all data from Producer..."
echo "GET ${KONG_URL}/producer/api/data"
curl -s ${KONG_URL}/producer/api/data | jq '.' || curl -s ${KONG_URL}/producer/api/data
echo ""

echo ""
echo "🔍 Testing Consumer service via Kong..."
echo "GET ${KONG_URL}/consumer/health"
curl -s ${KONG_URL}/consumer/health | jq '.' || curl -s ${KONG_URL}/consumer/health
echo ""

echo ""
echo "🎯 Triggering Producer to create new data via Consumer..."
echo "POST ${KONG_URL}/consumer/api/trigger-produce"
curl -X POST -s ${KONG_URL}/consumer/api/trigger-produce | jq '.' || curl -X POST -s ${KONG_URL}/consumer/api/trigger-produce
echo ""

echo ""
echo "📥 Consumer fetching data from Producer via Kong..."
echo "GET ${KONG_URL}/consumer/api/consume"
curl -s ${KONG_URL}/consumer/api/consume | jq '.' || curl -s ${KONG_URL}/consumer/api/consume
echo ""

echo ""
echo "✅ Testing complete!"
echo ""
echo "🌐 Access the admin interfaces:"
echo "  Producer Custom Admin: http://${KONG_HOST}:30080/producer/admin-dashboard"
echo "  Producer Django Admin: http://${KONG_HOST}:30080/producer/admin"
echo "  Consumer Custom Admin: http://${KONG_HOST}:30080/consumer/admin-dashboard"
echo "  Consumer Django Admin: http://${KONG_HOST}:30080/consumer/admin"
echo ""
echo "Note: If using port-forwarding instead, run:"
echo "  kubectl port-forward -n kong svc/kong-proxy 8000:8000"
echo "  Then access via:"
echo "    http://localhost:8000/producer/admin-dashboard (custom admin)"
echo "    http://localhost:8000/producer/admin (Django admin)"
echo "    http://localhost:8000/consumer/admin-dashboard (custom admin)"
echo "    http://localhost:8000/consumer/admin (Django admin)"
