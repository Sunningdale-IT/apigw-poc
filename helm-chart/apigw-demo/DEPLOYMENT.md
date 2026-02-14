# API Gateway POC Demo Suite - Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying the complete API Gateway POC demo suite to your AKS Kubernetes cluster with Traefik and cert-manager.

## Architecture Overview

The demo suite consists of:
- **Dogcatcher API** - Django REST API with multi-protocol authentication
- **Kong Gateway** - API Gateway with OIDC, JWT, API Key, and mTLS support
- **Model Citizen** - Consumer application demonstrating API usage
- **Certosaurus** - Certificate management portal
- **Keycloak** - Identity Provider for OIDC authentication
- **PostgreSQL** - Two database instances (dogcatcher-db and kong-db)

## Prerequisites

### Required Tools
- `kubectl` (v1.25+)
- `helm` (v3.10+)
- Access to your AKS cluster with appropriate permissions
- Docker for building container images

### Cluster Requirements
✅ **Already Configured:**
- Traefik Ingress Controller (installed)
- cert-manager (installed)
- Wildcard DNS: `*.jim00.pd.test-rig.nl` → Your AKS cluster

### Container Registry
You need to build and push Docker images to a container registry (Azure Container Registry, Docker Hub, etc.)

## Step 1: Build and Push Container Images

### 1.1 Build Docker Images

From the repository root:

```bash
# Build Dogcatcher API
docker build -t <your-registry>/dogcatcher-api:v1.0.0 ./app

# Build Kong with OIDC plugin
docker build -t <your-registry>/kong-oidc:v1.0.0 ./kong

# Build Model Citizen
docker build -t <your-registry>/model-citizen:v1.0.0 ./citizen-app

# Build Certosaurus
docker build -t <your-registry>/certosaurus:v1.0.0 ./certosaurus
```

### 1.2 Push Images to Registry

```bash
# Login to your registry
docker login <your-registry>

# Push all images
docker push <your-registry>/dogcatcher-api:v1.0.0
docker push <your-registry>/kong-oidc:v1.0.0
docker push <your-registry>/model-citizen:v1.0.0
docker push <your-registry>/certosaurus:v1.0.0
```

**Note:** Replace `<your-registry>` with your actual registry URL (e.g., `myregistry.azurecr.io`)

## Step 2: Configure cert-manager ClusterIssuer

Ensure you have a cert-manager ClusterIssuer configured. If not, create one:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
EOF
```

## Step 3: Create Custom Values File

Create a `my-values.yaml` file with your configuration:

```bash
cd helm-chart/apigw-demo
cp values-example.yaml my-values.yaml
```

Edit `my-values.yaml` and update the following:

```yaml
global:
  domain: jim00.pd.test-rig.nl
  storageClass: default  # or managed-premium for Azure

# Update all image repositories
dogcatcher:
  image:
    repository: <your-registry>/dogcatcher-api
    tag: "v1.0.0"
  
  # IMPORTANT: Change in production
  env:
    secretKey: "generate-a-random-secret-key-here"

dogcatcherDb:
  env:
    password: "secure-database-password-here"

kong:
  image:
    repository: <your-registry>/kong-oidc
    tag: "v1.0.0"

kongDb:
  env:
    password: "secure-kong-db-password-here"

citizen:
  image:
    repository: <your-registry>/model-citizen
    tag: "v1.0.0"
  
  env:
    secretKey: "generate-another-random-secret-key"

certosaurus:
  image:
    repository: <your-registry>/certosaurus
    tag: "v1.0.0"
  
  env:
    secretKey: "generate-yet-another-secret-key"

keycloak:
  env:
    adminPassword: "secure-keycloak-admin-password"
```

**Security Note:** For production, use Kubernetes Secrets or external secret management (Azure Key Vault, etc.)

## Step 4: Create Namespace

```bash
kubectl create namespace apigw-demo
```

## Step 5: Configure Image Pull Secret (if using private registry)

If using Azure Container Registry:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry>.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n apigw-demo
```

Update `my-values.yaml`:
```yaml
imagePullSecrets:
  - name: regcred
```

## Step 6: Deploy with Helm

### 6.1 Validate the Chart

```bash
helm lint -f my-values.yaml .
```

### 6.2 Dry Run (Preview)

```bash
helm install apigw-demo . \
  -f my-values.yaml \
  -n apigw-demo \
  --dry-run --debug
```

### 6.3 Install the Chart

```bash
helm install apigw-demo . \
  -f my-values.yaml \
  -n apigw-demo \
  --create-namespace
```

### 6.4 Monitor Deployment

```bash
# Watch pod status
kubectl get pods -n apigw-demo -w

# Check deployment status
helm status apigw-demo -n apigw-demo

# View all resources
kubectl get all,ingress,pvc -n apigw-demo
```

## Step 7: Verify TLS Certificates

Wait for cert-manager to issue certificates (1-5 minutes):

```bash
# Check certificate status
kubectl get certificates -n apigw-demo

# Check certificate details
kubectl describe certificate dogcatcher-tls -n apigw-demo

# Check cert-manager logs if issues
kubectl logs -n cert-manager deployment/cert-manager
```

All certificates should show `Ready: True`.

## Step 8: Initialize Applications

### 8.1 Create Dogcatcher Superuser

```bash
# Get the dogcatcher pod name
DOGCATCHER_POD=$(kubectl get pod -n apigw-demo -l app.kubernetes.io/component=dogcatcher -o jsonpath='{.items[0].metadata.name}')

# Create superuser
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- python manage.py createsuperuser
```

### 8.2 Load Test Data (Optional)

```bash
# Copy test data script to pod
kubectl cp scripts/load-test-data.sh $DOGCATCHER_POD:/tmp/ -n apigw-demo

# Run inside the pod
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- bash /tmp/load-test-data.sh
```

### 8.3 Configure Kong Routes

You need to configure Kong Gateway with routes and authentication plugins. Use the Kong Admin API:

```bash
# Get Kong Admin URL
KONG_ADMIN_URL="https://kong-admin.jim00.pd.test-rig.nl"

# Create a service pointing to dogcatcher
curl -X POST $KONG_ADMIN_URL/services \
  -d "name=dogcatcher" \
  -d "url=http://apigw-demo-dogcatcher:5000"

# Create public route (no auth)
curl -X POST $KONG_ADMIN_URL/services/dogcatcher/routes \
  -d "name=public-route" \
  -d "paths[]=/public" \
  -d "strip_path=true"

# Create API key protected route
curl -X POST $KONG_ADMIN_URL/services/dogcatcher/routes \
  -d "name=apikey-route" \
  -d "paths[]=/apikey" \
  -d "strip_path=true"

# Enable key-auth plugin
curl -X POST $KONG_ADMIN_URL/routes/apikey-route/plugins \
  -d "name=key-auth"

# Create a consumer and API key
curl -X POST $KONG_ADMIN_URL/consumers \
  -d "username=citizen-app"

curl -X POST $KONG_ADMIN_URL/consumers/citizen-app/key-auth \
  -d "key=citizen-api-key-2026"
```

**Alternative:** Use Kong Manager GUI at `https://kong-manager.jim00.pd.test-rig.nl`

## Step 9: Access the Applications

| Application | URL | Credentials |
|------------|-----|-------------|
| **Dogcatcher Admin** | https://dogcatcher.jim00.pd.test-rig.nl/admin/ | Created in Step 8.1 |
| **Kong Proxy** | https://kong.jim00.pd.test-rig.nl | N/A (API Gateway) |
| **Kong Admin API** | https://kong-admin.jim00.pd.test-rig.nl | No auth required (OSS) |
| **Kong Manager** | https://kong-manager.jim00.pd.test-rig.nl | No auth required (OSS) |
| **Model Citizen** | https://citizen.jim00.pd.test-rig.nl | N/A |
| **Certosaurus** | https://certosaurus.jim00.pd.test-rig.nl/login/ | Create on first visit |
| **Keycloak** | https://keycloak.jim00.pd.test-rig.nl | admin / (from values) |

## Step 10: Test the API Gateway

### Test Public Access (No Auth)
```bash
curl https://kong.jim00.pd.test-rig.nl/public/dogs/
```

### Test API Key Authentication
```bash
curl -H "X-API-Key: citizen-api-key-2026" \
  https://kong.jim00.pd.test-rig.nl/apikey/dogs/
```

### Test via Model Citizen App
Visit https://citizen.jim00.pd.test-rig.nl and browse found dogs.

## Troubleshooting

### Pods Not Starting

```bash
# Check pod logs
kubectl logs -n apigw-demo <pod-name>

# Check pod events
kubectl describe pod -n apigw-demo <pod-name>

# Check if images are accessible
kubectl get events -n apigw-demo --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it <dogcatcher-pod> -n apigw-demo -- nc -zv apigw-demo-dogcatcher-db 5432

# Check database logs
kubectl logs -n apigw-demo -l app.kubernetes.io/component=dogcatcher-db
```

### Certificate Issues

```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate request
kubectl get certificaterequest -n apigw-demo

# Check challenges
kubectl get challenges -n apigw-demo
```

### Ingress Not Working

```bash
# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik

# Verify ingress configuration
kubectl describe ingress -n apigw-demo
```

### DNS Issues

```bash
# Test DNS resolution
nslookup dogcatcher.jim00.pd.test-rig.nl

# Check if wildcard DNS points to correct IP
dig *.jim00.pd.test-rig.nl
```

## Upgrading the Deployment

To update the deployment:

```bash
# Update images in my-values.yaml, then:
helm upgrade apigw-demo . \
  -f my-values.yaml \
  -n apigw-demo
```

## Uninstalling

```bash
# Uninstall the Helm release
helm uninstall apigw-demo -n apigw-demo

# Delete PVCs (if you want to remove data)
kubectl delete pvc -n apigw-demo --all

# Delete namespace
kubectl delete namespace apigw-demo
```

## Production Considerations

### Security
1. **Secrets Management**: Use Azure Key Vault or Sealed Secrets
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Limit service account permissions
4. **Pod Security Standards**: Apply security contexts
5. **Image Scanning**: Scan images for vulnerabilities

### High Availability
1. **Database**: Consider Azure Database for PostgreSQL
2. **Redis**: Add Redis for Kong rate limiting
3. **Replicas**: Increase replica counts for critical services
4. **Pod Disruption Budgets**: Prevent simultaneous pod evictions

### Monitoring
1. **Prometheus**: Scrape metrics from Kong and Django
2. **Grafana**: Create dashboards
3. **Loki**: Aggregate logs
4. **Alerts**: Set up alerting rules

### Storage
```yaml
global:
  storageClass: managed-premium  # Use premium SSD for production
```

### Persistence
- Consider backup strategies for PostgreSQL databases
- Use Azure Backup or Velero for cluster-level backups

## Additional Configuration

### Enable mTLS Routes

See [docs/MTLS-SETUP.md](../../docs/MTLS-SETUP.md) for configuring mutual TLS authentication with Kong.

### Configure OIDC with Keycloak

See [docs/PROXY-MULTI-AUTH.md](../../docs/PROXY-MULTI-AUTH.md) for Keycloak OIDC configuration.

### Kong Configuration

For detailed Kong setup, see [docs/KONG-DEPLOYMENT.md](../../docs/KONG-DEPLOYMENT.md).

## Support

For issues or questions:
- Check existing documentation in `docs/`
- Review GitHub Issues
- Contact: info@sunningdale-it.nl

## Architecture Diagram

```
                                 Internet
                                    │
                                    ▼
                            ┌───────────────┐
                            │    Traefik    │
                            │    Ingress    │
                            └───────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
            │  Dogcatcher  │ │    Kong    │ │   Citizen  │
            │     API      │ │  Gateway   │ │   Portal   │
            └──────┬───────┘ └─────┬──────┘ └─────┬──────┘
                   │               │               │
            ┌──────▼──────┐ ┌─────▼──────┐       │
            │ PostgreSQL  │ │ PostgreSQL │       │
            │  (dogcat.)  │ │   (kong)   │       │
            └─────────────┘ └────────────┘       │
                                                  │
            ┌─────────────┐ ┌────────────┐       │
            │  Certosaurus  │ │ Keycloak   │───────┘
            │   (certs)   │ │   (OIDC)   │
            └─────────────┘ └────────────┘
```

## Next Steps

1. Configure Kong routes for different authentication methods
2. Set up monitoring and logging
3. Configure Keycloak realms and clients for OIDC
4. Generate and manage certificates with Certosaurus
5. Test all authentication flows

Enjoy your API Gateway POC Demo! 🚀
