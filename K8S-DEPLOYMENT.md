# Kubernetes Deployment - Quick Reference

## Overview

Complete Helm chart created at: `helm-chart/apigw-demo/`

The Helm chart deploys:
- **Dogcatcher API** (Django REST) with PostgreSQL database
- **Kong Gateway** with PostgreSQL database
- **Model Citizen** portal application  
- **Certosaurus** certificate management
- **Keycloak** OIDC identity provider

All components are configured with:
- Traefik Ingress with TLS via cert-manager
- Wildcard DNS: `*.jim00.pd.test-rig.nl`
- Persistent storage for databases
- Health checks and resource limits

## Quick Start

### Option 1: Interactive Script

```bash
./scripts/deploy-k8s.sh
```

The script will guide you through:
1. Checking prerequisites
2. Building Docker images (optional)
3. Creating configuration file
4. Deploying with Helm

### Option 2: Manual Deployment

```bash
cd helm-chart/apigw-demo

# 1. Create custom values
cp values-example.yaml my-values.yaml
# Edit my-values.yaml with your registry and configuration

# 2. Deploy
helm install apigw-demo . \
  -f my-values.yaml \
  -n apigw-demo \
  --create-namespace

# 3. Monitor
kubectl get pods -n apigw-demo -w
```

## Before Deploying

### 1. Build and Push Docker Images

```bash
# Set your registry
REGISTRY="your-registry.azurecr.io"
TAG="v1.0.0"

# Build images
docker build -t $REGISTRY/dogcatcher-api:$TAG ./app
docker build -t $REGISTRY/kong-oidc:$TAG ./kong
docker build -t $REGISTRY/model-citizen:$TAG ./citizen-app
docker build -t $REGISTRY/certosaurus:$TAG ./certosaurus

# Push images
docker push $REGISTRY/dogcatcher-api:$TAG
docker push $REGISTRY/kong-oidc:$TAG
docker push $REGISTRY/model-citizen:$TAG
docker push $REGISTRY/certosaurus:$TAG
```

### 2. Configure my-values.yaml

Update these critical values:

```yaml
# Image repositories - REQUIRED
dogcatcher:
  image:
    repository: your-registry/dogcatcher-api
    tag: v1.0.0

kong:
  image:
    repository: your-registry/kong-oidc
    tag: v1.0.0

# Security - CHANGE IN PRODUCTION
dogcatcher:
  env:
    secretKey: "generate-random-secret-here"

dogcatcherDb:
  env:
    password: "secure-password-here"

# Similar for kong, citizen, certosaurus, keycloak
```

### 3. Verify Prerequisites

```bash
# Check cluster connectivity
kubectl cluster-info

# Verify Traefik is installed
kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik

# Verify cert-manager is installed
kubectl get pods -n cert-manager

# Check DNS resolution
nslookup dogcatcher.jim00.pd.test-rig.nl
```

## After Deployment

### Check Status

```bash
# Watch pods
kubectl get pods -n apigw-demo -w

# Check all resources
kubectl get all,ingress,pvc -n apigw-demo

# View deployment info
helm status apigw-demo -n apigw-demo
```

### Wait for Certificates

```bash
# Check certificate status (wait for Ready: True)
kubectl get certificates -n apigw-demo
```

### Initialize Applications

```bash
# Create Dogcatcher superuser
DOGCATCHER_POD=$(kubectl get pod -n apigw-demo -l app.kubernetes.io/component=dogcatcher -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- python manage.py createsuperuser
```

## Access URLs

| Application | URL |
|------------|-----|
| Dogcatcher Admin | https://dogcatcher.jim00.pd.test-rig.nl/admin/ |
| Dogcatcher API | https://dogcatcher.jim00.pd.test-rig.nl/api/dogs/ |
| Kong Proxy | https://kong.jim00.pd.test-rig.nl/ |
| Kong Admin API | https://kong-admin.jim00.pd.test-rig.nl/ |
| Kong Manager | https://kong-manager.jim00.pd.test-rig.nl/ |
| Model Citizen | https://citizen.jim00.pd.test-rig.nl/ |
| Certosaurus | https://certosaurus.jim00.pd.test-rig.nl/login/ |
| Keycloak | https://keycloak.jim00.pd.test-rig.nl/ |

## Testing

```bash
# Test public API access
curl https://kong.jim00.pd.test-rig.nl/public/dogs/

# Test direct Dogcatcher access
curl https://dogcatcher.jim00.pd.test-rig.nl/api/dogs/
```

## Troubleshooting

### Pods not starting
```bash
kubectl logs -n apigw-demo <pod-name>
kubectl describe pod -n apigw-demo <pod-name>
```

### Certificate issues
```bash
kubectl describe certificate -n apigw-demo
kubectl logs -n cert-manager deployment/cert-manager
```

### Database connection errors
```bash
kubectl logs -n apigw-demo -l app.kubernetes.io/component=dogcatcher-db
```

## Updating

```bash
# Edit my-values.yaml, then:
helm upgrade apigw-demo . -f my-values.yaml -n apigw-demo
```

## Uninstalling

```bash
# Remove deployment
helm uninstall apigw-demo -n apigw-demo

# Delete data (optional)
kubectl delete pvc -n apigw-demo --all

# Delete namespace
kubectl delete namespace apigw-demo
```

## Documentation

For complete details, see:
- **[DEPLOYMENT.md](helm-chart/apigw-demo/DEPLOYMENT.md)** - Full deployment guide
- **[README.md](helm-chart/apigw-demo/README.md)** - Helm chart overview
- **[docs/KONG-DEPLOYMENT.md](docs/KONG-DEPLOYMENT.md)** - Kong configuration
- **[docs/MTLS-SETUP.md](docs/MTLS-SETUP.md)** - mTLS configuration

## Architecture

```
Internet → Traefik Ingress (TLS) → Services
                  ↓
    ┌─────────────┼──────────────┐
    │             │              │
Dogcatcher     Kong          Citizen
    │             │              
PostgreSQL    PostgreSQL     
    
Certosaurus     Keycloak
```

## Support

For issues: info@sunningdale-it.nl
