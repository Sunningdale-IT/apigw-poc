# Kong API Gateway PoC Helm Chart

This Helm chart deploys the complete Kong API Gateway proof of concept system, including:
- Producer microservice (Django REST API)
- Consumer microservice (Django REST API)
- Kong API Gateway

## Prerequisites

- Kubernetes cluster (tested on Azure AKS)
- Helm 3.x installed
- cert-manager installed in the cluster (for TLS/SSL certificates)
- nginx-ingress-controller or similar ingress controller
- DNS records configured to point to your ingress controller

## Installation

### Quick Install

```bash
# Install with default values
helm install apigw-poc ./helm-chart/apigw-poc

# Install in a specific namespace
helm install apigw-poc ./helm-chart/apigw-poc --create-namespace --namespace apigw-poc-system
```

### Custom Installation

```bash
# Install with custom domain
helm install apigw-poc ./helm-chart/apigw-poc \
  --set global.domainSuffix=yourdomain.com

# Install with custom image tags
helm install apigw-poc ./helm-chart/apigw-poc \
  --set producer.image.tag=v1.0.0 \
  --set consumer.image.tag=v1.0.0

# Install with custom values file
helm install apigw-poc ./helm-chart/apigw-poc \
  -f custom-values.yaml
```

## Configuration

The following table lists the configurable parameters and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.domainSuffix` | Domain suffix for all ingresses | `jim00.pd.test-rig.nl` |
| `global.tls.enabled` | Enable TLS/SSL | `true` |
| `global.tls.clusterIssuer` | cert-manager ClusterIssuer name | `letsencrypt-prod` |

### Producer Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `producer.enabled` | Enable producer deployment | `true` |
| `producer.replicaCount` | Number of replicas | `1` |
| `producer.image.repository` | Image repository | `jimleitch/producer-app` |
| `producer.image.tag` | Image tag | `latest` |
| `producer.image.pullPolicy` | Image pull policy | `Always` |
| `producer.service.type` | Service type | `ClusterIP` |
| `producer.service.port` | Service port | `80` |
| `producer.ingress.enabled` | Enable ingress | `true` |

### Consumer Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `consumer.enabled` | Enable consumer deployment | `true` |
| `consumer.replicaCount` | Number of replicas | `1` |
| `consumer.image.repository` | Image repository | `jimleitch/consumer-app` |
| `consumer.image.tag` | Image tag | `latest` |
| `consumer.image.pullPolicy` | Image pull policy | `Always` |
| `consumer.service.type` | Service type | `ClusterIP` |
| `consumer.service.port` | Service port | `80` |
| `consumer.ingress.enabled` | Enable ingress | `true` |
| `consumer.env.PRODUCER_API_URL` | Producer API URL via Kong | `http://kong-proxy.kong:8000/producer` |

### Kong Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `kong.enabled` | Enable Kong deployment | `true` |
| `kong.replicaCount` | Number of replicas | `1` |
| `kong.image.repository` | Image repository | `kong` |
| `kong.image.tag` | Image tag | `3.4` |
| `kong.service.type` | Service type | `ClusterIP` |
| `kong.service.ports.proxy` | Proxy port | `8000` |
| `kong.service.ports.admin` | Admin port | `8001` |
| `kong.ingress.enabled` | Enable ingress | `true` |

## Accessing the Applications

After installation, the applications will be accessible at:

- **Kong Gateway**: `https://kong.<domainSuffix>`
- **Producer Service**: `https://producer.<domainSuffix>`
- **Consumer Service**: `https://consumer.<domainSuffix>`

### Admin Interfaces

- **Producer Custom Dashboard**: `https://producer.<domainSuffix>/admin-dashboard`
- **Producer Django Admin**: `https://producer.<domainSuffix>/admin`
- **Consumer Custom Dashboard**: `https://consumer.<domainSuffix>/admin-dashboard`
- **Consumer Django Admin**: `https://consumer.<domainSuffix>/admin`

## DNS Configuration

You need to create DNS A records pointing to your ingress controller's external IP:

```bash
# Get the ingress external IP
kubectl get ingress -A

# Create DNS records:
# - kong.<domainSuffix> -> <ingress-ip>
# - producer.<domainSuffix> -> <ingress-ip>
# - consumer.<domainSuffix> -> <ingress-ip>
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade apigw-poc ./helm-chart/apigw-poc

# Upgrade with new image tags
helm upgrade apigw-poc ./helm-chart/apigw-poc \
  --set producer.image.tag=v1.1.0 \
  --set consumer.image.tag=v1.1.0
```

## Uninstalling

```bash
# Uninstall the chart
helm uninstall apigw-poc

# Note: Namespaces may need to be deleted manually
kubectl delete namespace producer consumer kong
```

## Troubleshooting

### Check Deployment Status

```bash
# List all resources
helm list
kubectl get all -n producer
kubectl get all -n consumer
kubectl get all -n kong

# Check pod logs
kubectl logs -n producer -l app=producer
kubectl logs -n consumer -l app=consumer
kubectl logs -n kong -l app=kong-proxy
```

### Check Ingress and Certificates

```bash
# Check ingress status
kubectl get ingress -A

# Check certificate status
kubectl get certificate -A
kubectl describe certificate -n kong kong-tls-cert
```

### Template Rendering

```bash
# Render templates without installing
helm template apigw-poc ./helm-chart/apigw-poc

# Render with custom values
helm template apigw-poc ./helm-chart/apigw-poc \
  --set global.domainSuffix=example.com
```

## Examples

### Development Setup (without TLS)

```yaml
# dev-values.yaml
global:
  tls:
    enabled: false

producer:
  ingress:
    enabled: false

consumer:
  ingress:
    enabled: false

kong:
  ingress:
    enabled: false
```

```bash
helm install apigw-poc ./helm-chart/apigw-poc -f dev-values.yaml
```

### Production Setup with Resource Limits

```yaml
# prod-values.yaml
producer:
  replicaCount: 3
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi

consumer:
  replicaCount: 3
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi

kong:
  replicaCount: 2
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

```bash
helm install apigw-poc ./helm-chart/apigw-poc -f prod-values.yaml
```

## Architecture

The Helm chart deploys the following resources:

- **3 Namespaces**: producer, consumer, kong
- **3 Deployments**: producer-app, consumer-app, kong-proxy
- **3 Services**: producer-service, consumer-service, kong-proxy
- **3 Ingresses**: producer-ingress, consumer-ingress, kong-ingress
- **1 ConfigMap**: kong-declarative-config (Kong routes configuration)

### Service Communication Flow

```
External User
    ↓
Ingress Controller
    ↓
    ├─→ Kong Gateway (kong namespace)
    ├─→ Producer Service (producer namespace)
    └─→ Consumer Service (consumer namespace)
            ↓
       (calls Producer via Kong)
```

## Support

For issues and questions, please refer to the main repository:
https://github.com/Sunningdale-IT/apigw-poc
