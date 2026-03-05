# APISIX Deployment Guide

This guide explains how to deploy Apache APISIX as a subchart alongside Kong in the apigw-demo Helm chart.

## Overview

APISIX is deployed using the official Apache APISIX Helm chart as a dependency. This approach provides:

- **Maintainability**: Leverage official updates from the APISIX project
- **Flexibility**: Easy to customize via values.yaml
- **Side-by-side deployment**: Run APISIX and Kong simultaneously for comparison and gradual migration

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    apigw-demo Chart                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │     Kong     │  │    APISIX    │  │   Keycloak   │ │
│  │   Gateway    │  │   Gateway    │  │     IdP      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │        │
│         └──────────────────┴──────────────────┘        │
│                           │                            │
│                    ┌──────┴──────┐                     │
│                    │  Dogcatcher  │                    │
│                    │ Model Citizen│                    │
│                    │  Certosaur   │                    │
│                    └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm 3.8+
- cert-manager (for TLS certificates)
- Traefik or another ingress controller

## Deployment Steps

### 1. Update Helm Dependencies

Before deploying, download the APISIX subchart:

```bash
cd helm-chart/apigw-demo
helm dependency update
```

This will:
- Download the APISIX chart from https://charts.apiseven.com
- Create a `charts/` directory with the APISIX chart
- Generate a `Chart.lock` file

### 2. Review Configuration

Edit `values.yaml` to customize APISIX settings:

```yaml
apisix:
  enabled: true  # Set to false to disable APISIX
  
  admin:
    credentials:
      admin: your-secure-admin-key  # CHANGE THIS
      viewer: your-secure-viewer-key  # CHANGE THIS
  
  ingress:
    enabled: true
    hosts:
      - host: apisix.your-domain.com  # Update domain
  
  dashboard:
    config:
      conf:
        authentication:
          users:
            - username: admin
              password: your-secure-password  # CHANGE THIS
```

### 3. Deploy with Helm

Deploy the complete stack:

```bash
helm install apigw-demo . \
  --namespace apigw-demo \
  --create-namespace \
  --set global.domain=your-domain.com \
  --set apisix.admin.credentials.admin='your-secure-key' \
  --set apisix.dashboard.config.conf.authentication.users[0].password='your-password'
```

Or upgrade an existing deployment:

```bash
helm upgrade apigw-demo . \
  --namespace apigw-demo \
  --reuse-values
```

### 4. Verify Deployment

Check APISIX pods:

```bash
kubectl get pods -n apigw-demo | grep apisix
```

Expected output:
```
apigw-demo-apisix-xxxxxxxxx-xxxxx           1/1     Running   0          2m
apigw-demo-apisix-dashboard-xxxxxxxxx-xxxxx 1/1     Running   0          2m
apigw-demo-apisix-etcd-0                    1/1     Running   0          2m
apigw-demo-apisix-etcd-1                    1/1     Running   0          2m
apigw-demo-apisix-etcd-2                    1/1     Running   0          2m
```

Check services:

```bash
kubectl get svc -n apigw-demo | grep apisix
```

Check ingresses:

```bash
kubectl get ingress -n apigw-demo | grep apisix
```

## Accessing APISIX

### APISIX Gateway

- **External URL**: https://apisix.jim00.pd.test-rig.nl (via ingress)
- **Internal Service**: `apigw-demo-apisix-gateway.apigw-demo.svc.cluster.local:80`

### APISIX Dashboard

- **External URL**: https://apisix-dashboard.jim00.pd.test-rig.nl
- **Default Credentials**: admin / admin (CHANGE IN PRODUCTION)

### Admin API

Access from within the cluster:

```bash
kubectl exec -it <apisix-pod> -n apigw-demo -- curl http://localhost:9180/apisix/admin/routes \
  -H "X-API-KEY: your-admin-key"
```

## Configuration Reference

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `apisix.enabled` | Enable/disable APISIX deployment | `true` |
| `apisix.gateway.type` | Gateway service type | `NodePort` |
| `apisix.admin.credentials.admin` | Admin API key | `edd1c9f034335f136f87ad84b625c8f1` |
| `apisix.etcd.replicaCount` | Number of etcd replicas | `3` |
| `apisix.etcd.persistence.size` | etcd PVC size | `8Gi` |
| `apisix.dashboard.enabled` | Enable APISIX Dashboard | `true` |
| `apisix.ingress.enabled` | Enable ingress for gateway | `true` |

### Plugin Configuration

APISIX comes pre-configured with common plugins. To add or remove plugins, edit `values.yaml`:

```yaml
apisix:
  apisix:
    plugins:
      - jwt-auth
      - key-auth
      - openid-connect
      - prometheus
      # Add more plugins as needed
```

See [APISIX Plugin Hub](https://apisix.apache.org/docs/apisix/plugins/jwt-auth/) for available plugins.

## Creating Routes

### Via Dashboard

1. Access https://apisix-dashboard.jim00.pd.test-rig.nl
2. Login with admin credentials
3. Navigate to Routes → Create
4. Configure upstream and plugins

### Via Admin API

Create a route to the Dogcatcher service:

```bash
curl "http://apisix-admin:9180/apisix/admin/routes/1" \
  -H "X-API-KEY: your-admin-key" \
  -X PUT -d '
{
  "uri": "/dogs/*",
  "upstream": {
    "type": "roundrobin",
    "nodes": {
      "dogcatcher:5000": 1
    }
  }
}'
```

## Comparing with Kong

Both API gateways are now available side-by-side:

| Feature | Kong | APISIX |
|---------|------|--------|
| **Gateway URL** | https://kong.jim00.pd.test-rig.nl | https://apisix.jim00.pd.test-rig.nl |
| **Admin UI** | Kong Manager | APISIX Dashboard |
| **Config Storage** | PostgreSQL | etcd |
| **Plugin Language** | Lua | Lua |
| **Admin API** | REST | REST |

## Troubleshooting

### APISIX pods not starting

Check etcd connectivity:

```bash
kubectl logs -n apigw-demo <apisix-pod> | grep etcd
```

### Dashboard login fails

Reset dashboard password:

```bash
helm upgrade apigw-demo . \
  --set apisix.dashboard.config.conf.authentication.users[0].password='newpassword'
```

### Routes not working

Check APISIX configuration:

```bash
kubectl exec -it <apisix-pod> -n apigw-demo -- cat /usr/local/apisix/conf/config.yaml
```

View logs:

```bash
kubectl logs -n apigw-demo <apisix-pod> -f
```

## Uninstalling APISIX

To remove only APISIX while keeping other services:

```bash
helm upgrade apigw-demo . \
  --set apisix.enabled=false
```

Clean up etcd PVCs:

```bash
kubectl delete pvc -n apigw-demo -l app.kubernetes.io/name=etcd
```

## Security Best Practices

1. **Change default credentials** before production deployment
2. **Use secrets** for sensitive values:
   ```bash
   kubectl create secret generic apisix-admin-key \
     --from-literal=key='your-secure-key' \
     -n apigw-demo
   ```
3. **Enable TLS** for all ingresses
4. **Restrict Admin API** access with network policies
5. **Enable etcd authentication** if storing sensitive data
6. **Regular updates**: Keep the APISIX subchart updated

## References

- [Apache APISIX Documentation](https://apisix.apache.org/docs/apisix/getting-started/)
- [APISIX Helm Chart](https://github.com/apache/apisix-helm-chart)
- [APISIX Plugin Hub](https://apisix.apache.org/plugins/)
- [Kong vs APISIX Comparison](https://apisix.apache.org/docs/apisix/comparison/)
