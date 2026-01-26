# Quick Start Guide

This guide will help you get the Kong API Gateway PoC up and running quickly.

## Prerequisites

- Kubernetes cluster (Minikube, kind, or any K8s cluster)
- Docker installed
- kubectl configured
- (Optional) curl and jq for testing

## Quick Setup with kind

```bash
# 1. Create a kind cluster
kind create cluster

# 2. Build Docker images
./scripts/build-images.sh

# 3. Load images into kind
./scripts/load-images-kind.sh

# 4. Deploy everything
./scripts/deploy.sh

# 5. Test the setup
./scripts/test-api.sh
```

## Quick Setup with Minikube

```bash
# 1. Start Minikube
minikube start

# 2. Use Minikube's Docker daemon
eval $(minikube docker-env)

# 3. Build Docker images
./scripts/build-images.sh

# 4. Deploy everything
./scripts/deploy.sh

# 5. Test the setup
./scripts/test-api.sh
```

## Accessing Admin Interfaces

After deployment, access the admin interfaces at:

- **Producer Custom Dashboard**: http://localhost:30080/producer/admin-dashboard
- **Producer Django Admin**: http://localhost:30080/producer/admin  
- **Consumer Custom Dashboard**: http://localhost:30080/consumer/admin-dashboard
- **Consumer Django Admin**: http://localhost:30080/consumer/admin

## Testing the API

### Check Health

```bash
# Producer health
curl http://localhost:30080/producer/health

# Consumer health
curl http://localhost:30080/consumer/health
```

### Produce Data

```bash
# Generate new data via Producer
curl -X POST http://localhost:30080/producer/api/produce
```

### Consume Data

```bash
# Consumer fetches data from Producer via Kong
curl http://localhost:30080/consumer/api/consume
```

### Trigger Producer from Consumer

```bash
# Consumer tells Producer to generate data (via Kong)
curl -X POST http://localhost:30080/consumer/api/trigger-produce
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
```

### Can't access services

```bash
# For Minikube users
minikube service kong-proxy -n kong --url

# For kind/Docker Desktop
# Services are accessible at localhost:30080
```

### Images not found

```bash
# For kind - ensure images are loaded
./scripts/load-images-kind.sh

# For Minikube - ensure you're using Minikube's Docker
eval $(minikube docker-env)
./scripts/build-images.sh
```

## Architecture Overview

```
User/Client
    ↓
Kong Gateway (port 30080)
    ↓
    ├─→ /producer/* → Producer Service (namespace: producer)
    └─→ /consumer/* → Consumer Service (namespace: consumer)
                          ↓
                     (calls Producer via Kong)
```

## Key Benefits Demonstrated

1. **Centralized Routing**: All traffic flows through Kong
2. **Service Discovery**: Services use Kong routes, not direct URLs
3. **Namespace Isolation**: Each service in its own namespace
4. **Easy Configuration**: Declarative Kong config via ConfigMap
5. **Admin Visibility**: Dual admin interfaces per service

For more details, see the main [README.md](README.md)
