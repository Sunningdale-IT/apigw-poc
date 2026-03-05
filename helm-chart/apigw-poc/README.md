# apigw-poc Helm Chart

This Helm chart deploys the API Gateway POC with Kong and supporting infrastructure.

## Features

- **Kong Gateway**: API Gateway with multi-protocol authentication
- **OAuth2 Proxy**: Keycloak integration for Kong Manager

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- cert-manager (for TLS certificates)
- Ingress controller (e.g., Traefik, NGINX)

## Installation

### Quick Start

```bash
# Install with default values
helm install apigw-poc ./helm-chart/apigw-poc

# Or with custom domain
helm install apigw-poc ./helm-chart/apigw-poc \
  --set global.domainSuffix=yourdomain.com
```

### Production Installation

For production, create a custom values file:

```yaml
# custom-values.yaml
global:
  domainSuffix: yourdomain.com
  storageClass: fast-ssd
```

Then install:

```bash
helm install apigw-poc ./helm-chart/apigw-poc -f custom-values.yaml
```

## Configuration

```bash
helm upgrade apigw-poc ./helm-chart/apigw-poc -f custom-values.yaml
```

## Uninstalling

```bash
helm uninstall apigw-poc
```

**Note**: PersistentVolumeClaims (PVCs) are not automatically deleted. Delete them manually if needed:

```bash
kubectl delete pvc -l app.kubernetes.io/instance=apigw-poc
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/instance=apigw-poc
```

## Security Considerations

⚠️ **Important**: Change all default passwords before deploying to production!

- Use TLS for all communications
- Regularly update images to get security patches

## Support

For issues and questions:
- GitHub Issues: https://github.com/Sunningdale-IT/apigw-poc/issues

## License

See the main repository for license information.
