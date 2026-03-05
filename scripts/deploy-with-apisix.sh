#!/bin/bash
#
# deploy-with-apisix.sh
# Deploys the apigw-demo helm chart with APISIX enabled
#

set -e

NAMESPACE="${NAMESPACE:-apigw-demo}"
RELEASE_NAME="${RELEASE_NAME:-apigw-demo}"
HELM_TIMEOUT="${HELM_TIMEOUT:-15m}"  # Increased default timeout
HELM_WAIT="${HELM_WAIT:-true}"  # Can be disabled by setting HELM_WAIT=false

# Determine repository root (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHART_DIR="$REPO_ROOT/helm-chart/apigw-demo"

echo "========================================="
echo "APISIX + Kong Deployment Script"
echo "========================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE_NAME"
echo "Chart: $CHART_DIR"
echo ""

# Navigate to chart directory
cd "$CHART_DIR"

# Step 1: Update Helm dependencies
echo "Step 1: Updating Helm dependencies..."
helm dependency update
echo "✅ Dependencies updated"
echo ""

# Step 2: Create namespace if it doesn't exist
echo "Step 2: Creating namespace (if needed)..."
kubectl create namespace "$NAMESPACE" 2>/dev/null || echo "Namespace $NAMESPACE already exists"
echo "✅ Namespace ready"
echo ""

# Step 3: Generate secure credentials (if not provided via environment)
if [ -z "$APISIX_ADMIN_KEY" ]; then
    APISIX_ADMIN_KEY=$(openssl rand -hex 32)
    echo "Generated APISIX Admin Key: $APISIX_ADMIN_KEY"
fi

if [ -z "$APISIX_DASHBOARD_PASSWORD" ]; then
    APISIX_DASHBOARD_PASSWORD=$(openssl rand -base64 16)
    echo "Generated APISIX Dashboard Password: $APISIX_DASHBOARD_PASSWORD"
fi

# Save credentials to file for reference
CREDS_FILE="apisix-credentials.txt"
cat > "$CREDS_FILE" <<EOF
APISIX Deployment Credentials
==============================
Generated: $(date)

Admin API Key: $APISIX_ADMIN_KEY
Dashboard Username: admin
Dashboard Password: $APISIX_DASHBOARD_PASSWORD

⚠️  IMPORTANT: Store these credentials securely and delete this file after saving them!

Admin API Usage:
curl "http://apigw-demo-apisix-admin:9180/apisix/admin/routes" \\
  -H "X-API-KEY: $APISIX_ADMIN_KEY"

Dashboard Access:
URL: https://apisix-dashboard.jim00.pd.test-rig.nl
Username: admin
Password: $APISIX_DASHBOARD_PASSWORD
EOF

echo ""
echo "✅ Credentials saved to: $CREDS_FILE"
echo ""

# Step 4: Deploy with Helm
echo "Step 3: Deploying with Helm..."
echo ""
echo "Settings:"
echo "  - APISIX: enabled"
echo "  - etcd replicas: 3"
echo "  - Dashboard: enabled"
echo "  - Ingress: enabled"
echo "  - Helm timeout: $HELM_TIMEOUT"
echo "  - Wait for ready: $HELM_WAIT"
echo ""

if [ "$HELM_WAIT" = "true" ]; then
  helm upgrade --install "$RELEASE_NAME" . \
    --namespace "$NAMESPACE" \
    --set apisix.enabled=true \
    --set "apisix.admin.credentials.admin=$APISIX_ADMIN_KEY" \
    --set "apisix.dashboard.config.conf.authentication.users[0].password=$APISIX_DASHBOARD_PASSWORD" \
    --wait \
    --timeout "$HELM_TIMEOUT"
else
  helm upgrade --install "$RELEASE_NAME" . \
    --namespace "$NAMESPACE" \
    --set apisix.enabled=true \
    --set "apisix.admin.credentials.admin=$APISIX_ADMIN_KEY" \
    --set "apisix.dashboard.config.conf.authentication.users[0].password=$APISIX_DASHBOARD_PASSWORD"
fi

echo ""
echo "✅ Deployment complete!"
echo ""

# If we didn't wait, give instructions for monitoring
if [ "$HELM_WAIT" = "false" ]; then
  echo "⏳ Deployment started but not waiting for completion."
  echo "   Monitor progress with:"
  echo "   kubectl get pods -n $NAMESPACE -w"
  echo ""
fi

# Step 5: Verify deployment
echo "Step 4: Verifying deployment..."
echo ""

echo "APISIX Pods:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=apisix"
echo ""

echo "etcd Pods:"
kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=etcd"
echo ""

echo "APISIX Services:"
kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/name=apisix"
echo ""

echo "APISIX Ingresses:"
kubectl get ingress -n "$NAMESPACE" | grep apisix || echo "No APISIX ingresses found (check ingress.enabled in values)"
echo ""

echo "========================================="
echo "Deployment Summary"
echo "========================================="
echo ""
echo "✅ APISIX API Gateway deployed successfully!"
echo ""
echo "📝 Credentials stored in: $CREDS_FILE"
echo "   Please save these credentials and delete the file!"
echo ""
echo "🌐 Access Points:"
echo "   - APISIX Gateway: https://apisix.jim00.pd.test-rig.nl"
echo "   - APISIX Dashboard: https://apisix-dashboard.jim00.pd.test-rig.nl"
echo "   - Kong Gateway: https://kong.jim00.pd.test-rig.nl"
echo "   - Kong Manager: https://kong-manager.jim00.pd.test-rig.nl"
echo ""
echo "📚 Next Steps:"
echo "   1. Save the credentials from $CREDS_FILE"
echo "   2. Access the APISIX Dashboard to configure routes"
echo "   3. Review documentation: helm-chart/apigw-demo/APISIX-DEPLOYMENT.md"
echo ""
echo "🔧 Useful Commands:"
echo "   # View APISIX logs"
echo "   kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=apisix -f"
echo ""
echo "   # Access APISIX pod"
echo "   kubectl exec -it -n $NAMESPACE \$(kubectl get pod -n $NAMESPACE -l app.kubernetes.io/name=apisix -o jsonpath='{.items[0].metadata.name}') -- sh"
echo ""
echo "   # Test Admin API"
echo "   kubectl exec -it -n $NAMESPACE \$(kubectl get pod -n $NAMESPACE -l app.kubernetes.io/name=apisix -o jsonpath='{.items[0].metadata.name}') -- curl http://localhost:9180/apisix/admin/routes -H \"X-API-KEY: $APISIX_ADMIN_KEY\""
echo ""
echo "========================================="
