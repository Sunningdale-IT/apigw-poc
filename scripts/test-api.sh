#!/bin/bash

# Test the Kong API Gateway setup
echo "🧪 Testing Kong API Gateway PoC..."
echo ""

# Use external AKS URLs
KONG_URL="https://kong.jim00.pd.test-rig.nl"
PRODUCER_URL="https://producer.jim00.pd.test-rig.nl"
CONSUMER_URL="https://consumer.jim00.pd.test-rig.nl"

echo "Using external AKS URLs:"
echo "  Kong: ${KONG_URL}"
echo "  Producer: ${PRODUCER_URL}"
echo "  Consumer: ${CONSUMER_URL}"

echo ""
echo "🔍 Testing Producer service..."
echo "GET ${PRODUCER_URL}/health"
curl -s ${PRODUCER_URL}/health | jq '.' || curl -s ${PRODUCER_URL}/health
echo ""

echo ""
echo "📊 Getting all data from Producer..."
echo "GET ${PRODUCER_URL}/api/data"
curl -s ${PRODUCER_URL}/api/data | jq '.' || curl -s ${PRODUCER_URL}/api/data
echo ""

echo ""
echo "🔍 Testing Consumer service..."
echo "GET ${CONSUMER_URL}/health"
curl -s ${CONSUMER_URL}/health | jq '.' || curl -s ${CONSUMER_URL}/health
echo ""

echo ""
echo "🎯 Triggering Producer to create new data via Consumer..."
echo "POST ${CONSUMER_URL}/api/trigger-produce"
curl -X POST -s ${CONSUMER_URL}/api/trigger-produce | jq '.' || curl -X POST -s ${CONSUMER_URL}/api/trigger-produce
echo ""

echo ""
echo "📥 Consumer fetching data from Producer via Kong..."
echo "GET ${CONSUMER_URL}/api/consume"
curl -s ${CONSUMER_URL}/api/consume | jq '.' || curl -s ${CONSUMER_URL}/api/consume
echo ""

echo ""
echo "🔍 Testing Kong Gateway routes..."
echo "GET ${KONG_URL}/producer/health"
curl -s ${KONG_URL}/producer/health | jq '.' || curl -s ${KONG_URL}/producer/health
echo ""

echo ""
echo "✅ Testing complete!"
echo ""
echo "🌐 Access the admin interfaces:"
echo "  Producer Custom Admin: ${PRODUCER_URL}/admin-dashboard"
echo "  Producer Django Admin: ${PRODUCER_URL}/admin"
echo "  Consumer Custom Admin: ${CONSUMER_URL}/admin-dashboard"
echo "  Consumer Django Admin: ${CONSUMER_URL}/admin"
echo "  Kong Gateway: ${KONG_URL}"
