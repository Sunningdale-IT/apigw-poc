# API Gateway POC Demo Suite - Helm Chart

Complete Helm chart for deploying the API Gateway POC demo suite to Kubernetes.

## Quick Start

```bash
# 1. Build and push Docker images (update registry URLs)
docker build -t your-registry/dogcatcher-api:v1.0.0 ../../app
docker build -t your-registry/kong-oidc:v1.0.0 ../../kong
docker build -t your-registry/model-citizen:v1.0.0 ../../citizen-app
docker build -t your-registry/certosaurus:v1.0.0 ../../certosaur

# 2. Create custom values file
cp values-example.yaml my-values.yaml
# Edit my-values.yaml with your registry and configuration

# 3. Deploy
helm install apigw-demo . -f my-values.yaml -n apigw-demo --create-namespace

# 4. Monitor deployment
kubectl get pods -n apigw-demo -w
```

## Components

- **Dogcatcher API** - Django REST API with multi-protocol authentication
- **Kong Gateway** - API Gateway with routes and plugins
- **Model Citizen** - Consumer application
- **Certosaurus** - Certificate management
- **Keycloak** - OIDC Identity Provider
- **PostgreSQL** - Two database instances

## Documentation

For complete deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

## Configuration

All configuration is done through `values.yaml`. Key sections:

- `global.domain` - Your wildcard DNS domain
- `*.image.repository` - Container registry URLs
- `*.env.secretKey` - Secret keys (change in production!)
- `*.ingress.host` - Hostnames for each service

## Requirements

- Kubernetes 1.25+
- Helm 3.10+
- Traefik Ingress Controller
- cert-manager
- Wildcard DNS pointing to cluster

## Support

For issues or questions, see [DEPLOYMENT.md](./DEPLOYMENT.md) or contact info@sunningdale-it.nl
