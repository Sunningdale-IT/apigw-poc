# Kong API Gateway Deployment Guide

This guide covers deploying Kong API Gateway on Kubernetes using Helm, and configuring it to proxy requests from Model Citizen to the Dogcatcher API with API key authentication.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Model Citizen  │────▶│  Kong Gateway   │────▶│  Dogcatcher API  │────▶│  PostgreSQL │
│   (port 5002)   │     │   (port 8000)   │     │   (port 5000)    │     │             │
└─────────────────┘     └─────────────────┘     └──────────────────┘     └─────────────┘
                              │
                              ▼
                        API Key Auth
                        Rate Limiting
                        Logging
```

## Prerequisites

- Kubernetes cluster (1.21+)
- Helm 3.x installed
- kubectl configured to access your cluster
- Sufficient cluster resources (Kong requires ~512MB RAM minimum)

## Step 1: Add Kong Helm Repository

```bash
helm repo add kong https://charts.konghq.com
helm repo update
```

## Step 2: Create Kong Namespace

```bash
kubectl create namespace kong
```

## Step 3: Deploy Kong

### Option A: Kong in DB-less Mode (Recommended for simplicity)

Create a values file for Kong:

```bash
cat > kong-values.yaml << 'EOF'
# Kong DB-less mode configuration
ingressController:
  enabled: true
  installCRDs: false

proxy:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 80
    containerPort: 8000
  tls:
    enabled: false

admin:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 8001
    containerPort: 8001

env:
  database: "off"
  # Enable plugins
  plugins: bundled

# Resource limits
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 512Mi
EOF
```

Install Kong:

```bash
helm install kong kong/kong \
  --namespace kong \
  --values kong-values.yaml \
  --wait
```

### Option B: Kong with PostgreSQL Database

For production environments requiring persistent configuration:

```bash
cat > kong-values-db.yaml << 'EOF'
# Kong with PostgreSQL
ingressController:
  enabled: true
  installCRDs: false

proxy:
  enabled: true
  type: ClusterIP

admin:
  enabled: true
  type: ClusterIP

postgresql:
  enabled: true
  auth:
    username: kong
    password: kong123
    database: kong

env:
  database: postgres
  pg_host: kong-postgresql
  pg_user: kong
  pg_password: kong123
  pg_database: kong

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 100m
    memory: 512Mi
EOF

helm install kong kong/kong \
  --namespace kong \
  --values kong-values-db.yaml \
  --wait
```

## Step 4: Verify Kong Installation

```bash
# Check pods are running
kubectl get pods -n kong

# Check services
kubectl get svc -n kong

# Test Kong admin API (from within cluster or with port-forward)
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001 &
curl http://localhost:8001/status
```

## Step 5: Configure Kong for Dogcatcher API

### Create Kong Configuration CRDs

Create the following Kubernetes manifests:

```bash
cat > kong-dogcatcher-config.yaml << 'EOF'
---
# Kong Service - Backend Dogcatcher API
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-key-auth
  namespace: kong
plugin: key-auth
config:
  key_names:
    - X-API-Key
    - apikey
  hide_credentials: true
---
# Rate limiting plugin (optional but recommended)
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-rate-limit
  namespace: kong
plugin: rate-limiting
config:
  minute: 100
  policy: local
---
# Logging plugin (optional)
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: dogcatcher-request-log
  namespace: kong
plugin: file-log
config:
  path: /dev/stdout
  reopen: true
EOF

kubectl apply -f kong-dogcatcher-config.yaml
```

### Create Ingress for Dogcatcher API

```bash
cat > kong-dogcatcher-ingress.yaml << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dogcatcher-api
  namespace: default  # Change to your dogcatcher namespace
  annotations:
    konghq.com/plugins: dogcatcher-key-auth,dogcatcher-rate-limit
    konghq.com/strip-path: "true"
spec:
  ingressClassName: kong
  rules:
    - http:
        paths:
          - path: /dogcatcher
            pathType: Prefix
            backend:
              service:
                name: dogcatcher-api  # Your dogcatcher service name
                port:
                  number: 5000
EOF

kubectl apply -f kong-dogcatcher-ingress.yaml
```

## Step 6: Create API Keys for Consumers

### Create a Consumer (Model Citizen App)

```bash
cat > kong-consumers.yaml << 'EOF'
---
apiVersion: configuration.konghq.com/v1
kind: KongConsumer
metadata:
  name: model-citizen
  namespace: kong
  annotations:
    kubernetes.io/ingress.class: kong
username: model-citizen
custom_id: model-citizen-app
EOF

kubectl apply -f kong-consumers.yaml
```

### Create API Key Secret

```bash
# Generate a random API key
API_KEY=$(openssl rand -hex 32)
echo "Generated API Key: ${API_KEY}"

# Create secret with API key
cat > kong-api-key-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: model-citizen-apikey
  namespace: kong
  labels:
    konghq.com/credential: key-auth
stringData:
  key: "${API_KEY}"
  kongCredType: key-auth
EOF

kubectl apply -f kong-api-key-secret.yaml
```

### Associate API Key with Consumer

```bash
cat > kong-consumer-credential.yaml << 'EOF'
apiVersion: configuration.konghq.com/v1
kind: KongConsumer
metadata:
  name: model-citizen
  namespace: kong
  annotations:
    kubernetes.io/ingress.class: kong
username: model-citizen
credentials:
  - model-citizen-apikey
EOF

kubectl apply -f kong-consumer-credential.yaml
```

## Step 7: Configure Model Citizen to Use Kong

Update the Model Citizen Helm values:

```yaml
config:
  # Kong proxy service URL
  apiGatewayUrl: "http://kong-kong-proxy.kong.svc.cluster.local/dogcatcher/api"
  dogcatcherPublicUrl: "https://dogcatcher.example.com"
```

Or set via Helm install:

```bash
helm install model-citizen ./helm-chart/model-citizen \
  --set image.repository=YOUR_DOCKERHUB_USERNAME/model-citizen \
  --set config.apiGatewayUrl="http://kong-kong-proxy.kong.svc.cluster.local/dogcatcher/api" \
  --set config.dogcatcherPublicUrl="https://dogcatcher.example.com"
```

## Step 8: Test the Setup

### Port-forward Kong Proxy

```bash
kubectl port-forward -n kong svc/kong-kong-proxy 8000:80 &
```

### Test without API Key (should fail)

```bash
curl -i http://localhost:8000/dogcatcher/api/dogs/
# Expected: 401 Unauthorized
```

### Test with API Key (should succeed)

```bash
curl -i http://localhost:8000/dogcatcher/api/dogs/ \
  -H "X-API-Key: YOUR_API_KEY_HERE"
# Expected: 200 OK with list of dogs
```

## Kong Manager UI (Optional)

For easier management, you can enable Kong Manager:

```yaml
# Add to kong-values.yaml
manager:
  enabled: true
  type: ClusterIP
  http:
    enabled: true
    servicePort: 8002
```

Access via port-forward:

```bash
kubectl port-forward -n kong svc/kong-kong-manager 8002:8002
# Open http://localhost:8002 in browser
```

## Troubleshooting

### Check Kong Logs

```bash
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=100
```

### Check Kong Configuration

```bash
kubectl port-forward -n kong svc/kong-kong-admin 8001:8001 &

# List services
curl http://localhost:8001/services

# List routes
curl http://localhost:8001/routes

# List consumers
curl http://localhost:8001/consumers

# List plugins
curl http://localhost:8001/plugins
```

### Common Issues

1. **502 Bad Gateway**: Dogcatcher service not reachable from Kong namespace
   - Check service DNS: `dogcatcher-api.default.svc.cluster.local`
   - Verify network policies allow traffic

2. **401 Unauthorized**: API key not configured correctly
   - Verify consumer and credential are created
   - Check key-auth plugin is attached to the route

3. **Connection Refused**: Kong proxy not running
   - Check Kong pods: `kubectl get pods -n kong`
   - Check Kong logs for errors

## Cleanup

```bash
# Remove Kong
helm uninstall kong -n kong

# Remove namespace
kubectl delete namespace kong

# Remove CRDs (if installed)
kubectl delete crd kongplugins.configuration.konghq.com
kubectl delete crd kongconsumers.configuration.konghq.com
kubectl delete crd kongingresses.configuration.konghq.com
```

## Next Steps

- Configure TLS termination at Kong
- Set up Kong for multiple environments (dev, staging, prod)
- Implement additional plugins (CORS, request transformation, caching)
- Set up monitoring with Prometheus/Grafana
