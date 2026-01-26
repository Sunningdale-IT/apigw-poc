# Quick Start Guide

This guide will help you get the Kong API Gateway PoC up and running on Azure AKS.

## Prerequisites

- Azure Kubernetes Service (AKS) cluster with cert-manager installed
- Docker Hub account (images hosted at https://hub.docker.com/repository/docker/jimleitch)
- Docker installed (for building images)
- kubectl configured to access your AKS cluster
- Helm 3.x (for Helm deployment option)
- (Optional) curl and jq for testing

## Quick Setup with Azure AKS

### Option 1: Deploy with Helm (Recommended)

```bash
# 1. Build and push Docker images (requires Docker Hub login)
docker login
./scripts/build-and-push.sh

# 2. Install with Helm
helm install apigw-poc ./helm-chart/apigw-poc

# 3. Wait for ingress to get external IP
kubectl get ingress -A -w

# 4. Configure DNS records
# Create A records pointing to the ingress external IP:
# - kong.jim00.pd.test-rig.nl
# - producer.jim00.pd.test-rig.nl
# - consumer.jim00.pd.test-rig.nl

# 5. Test the setup (after DNS propagation)
./scripts/test-api.sh
```

For custom configuration:
```bash
# Install with custom domain
helm install apigw-poc ./helm-chart/apigw-poc \
  --set global.domainSuffix=yourdomain.com
```

### Option 2: Deploy with kubectl (Manual)

```bash
# 1. Build and push Docker images (requires Docker Hub login)
docker login
./scripts/build-and-push.sh

# 2. Deploy to AKS
./scripts/deploy.sh

# 3. Wait for ingress to get external IP
kubectl get ingress -A -w

# 4. Configure DNS records
# Create A records pointing to the ingress external IP:
# - kong.jim00.pd.test-rig.nl
# - producer.jim00.pd.test-rig.nl
# - consumer.jim00.pd.test-rig.nl

# 5. Test the setup (after DNS propagation)
./scripts/test-api.sh
```

## Accessing Admin Interfaces

After deployment and DNS configuration, access the admin interfaces at:

- **Producer Custom Dashboard**: https://producer.jim00.pd.test-rig.nl/admin-dashboard
- **Producer Django Admin**: https://producer.jim00.pd.test-rig.nl/admin  
- **Consumer Custom Dashboard**: https://consumer.jim00.pd.test-rig.nl/admin-dashboard
- **Consumer Django Admin**: https://consumer.jim00.pd.test-rig.nl/admin
- **Kong Gateway**: https://kong.jim00.pd.test-rig.nl

## Testing the API

### Check Health

```bash
# Producer health
curl https://producer.jim00.pd.test-rig.nl/health

# Consumer health
curl https://consumer.jim00.pd.test-rig.nl/health
```

### Produce Data

```bash
# Generate new data via Producer
curl -X POST https://producer.jim00.pd.test-rig.nl/api/produce
```

### Consume Data

```bash
# Consumer fetches data from Producer via Kong
curl https://consumer.jim00.pd.test-rig.nl/api/consume
```

### Trigger Producer from Consumer

```bash
# Consumer tells Producer to generate data (via Kong)
curl -X POST https://consumer.jim00.pd.test-rig.nl/api/trigger-produce
```

## Viewing Status

```bash
# Check deployment status
./scripts/status.sh

# View logs
kubectl logs -n kong -l app=kong-proxy -f
kubectl logs -n producer -l app=producer -f
kubectl logs -n consumer -l app=consumer -f
```

## Cleanup

### If deployed with Helm:
```bash
# Uninstall the Helm release
helm uninstall apigw-poc

# Optionally delete the namespaces
kubectl delete namespace producer consumer kong
```

### If deployed with kubectl:
```bash
# Remove all resources
./scripts/cleanup.sh
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n kong
kubectl get pods -n producer
kubectl get pods -n consumer

# Describe problematic pod
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>
```

### Can't access services

```bash
# Check ingress status
kubectl get ingress -A

# Verify DNS records are pointing to the correct IP
nslookup kong.jim00.pd.test-rig.nl
nslookup producer.jim00.pd.test-rig.nl
nslookup consumer.jim00.pd.test-rig.nl

# Check cert-manager certificate status
kubectl get certificate -A
kubectl describe certificate -n kong kong-tls-cert
```

### Images not found

```bash
# Verify images are available on Docker Hub
# Visit https://hub.docker.com/r/jimleitch/producer-app
# Visit https://hub.docker.com/r/jimleitch/consumer-app

# Or pull them directly to test
docker pull jimleitch/producer-app:latest
docker pull jimleitch/consumer-app:latest
```

### TLS/Certificate Issues

```bash
# Check certificate status
kubectl get certificate -A
kubectl describe certificate -n kong kong-tls-cert

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Verify ClusterIssuer exists
kubectl get clusterissuer
```

## Architecture Overview

```
User/Client (External)
    ↓ HTTPS
Ingress Controller (nginx)
    ↓
    ├─→ kong.jim00.pd.test-rig.nl → Kong Gateway (namespace: kong)
    ├─→ producer.jim00.pd.test-rig.nl → Producer Service (namespace: producer)  
    └─→ consumer.jim00.pd.test-rig.nl → Consumer Service (namespace: consumer)
                                              ↓
                                         (calls Producer via Kong)
```

## Key Benefits Demonstrated

1. **External Access**: All services accessible via HTTPS with proper domain names
2. **Centralized Routing**: Traffic flows through Kong and Ingress
3. **Service Discovery**: Services use Kong routes, not direct URLs
4. **Namespace Isolation**: Each service in its own namespace
5. **TLS/SSL**: Automatic certificate management via cert-manager
6. **Easy Configuration**: Declarative Kong config via ConfigMap
7. **Admin Visibility**: Dual admin interfaces per service

For more details, see the main [README.md](README.md)
