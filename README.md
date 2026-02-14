# Dogcatcher API Gateway POC

A proof-of-concept demonstrating API Gateway patterns with a Django-based dog catcher application. This project showcases multi-protocol authentication (Plain, API Key, JWT, mTLS, OIDC), API Gateway configuration with Kong, certificate management, and cloud-native Kubernetes deployment.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Model Citizen  │────▶│  Kong Gateway   │────▶│  Dogcatcher API │
│  (Django App)   │     │  (API Gateway)  │     │  (Django REST)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
        ┌──────────────────────┼────────────────────────┤
        │                      │                        │
        ▼                      │                        ▼
┌─────────────────┐            │                ┌─────────────────┐
│   Certosaurus     │            │                │   PostgreSQL    │
│ (Certificate    │            │                │    Server       │
│  Management)    │            │                │  ┌───────────┐  │
└─────────────────┘            │                │  │  kong db  │  │
                               ▼                │  │ dogcatcher│  │
                        ┌─────────────────┐     │  │ keycloak  │  │
                        │    Keycloak     │     │  └───────────┘  │
                        │ (Identity Prov) │     └─────────────────┘
                        └─────────────────┘
```

### API Gateway Routes (Kong)

Kong API Gateway provides 6 authentication methods via different URL paths:

| Route | Authentication | Description | Example |
|-------|----------------|-------------|---------|
| `/public/*` | None | Open access, no credentials | `curl http://localhost:8000/public/dogs/` |
| `/apikey/*` | API Key | Kong validates X-API-Key header | `curl -H 'X-API-Key: citizen-api-key-2026' http://localhost:8000/apikey/dogs/` |
| `/jwt/*` | JWT Token | Kong validates JWT signature & expiry | `curl -H 'Authorization: Bearer <token>' http://localhost:8000/jwt/dogs/` |
| `/mtls/*` | Client Cert | Mutual TLS authentication | `curl --cert client.crt --key client.key https://localhost:8443/mtls/dogs/` |
| `/oidc/*` | OIDC | OpenID Connect via Keycloak | `curl -H 'Authorization: Bearer <oidc-token>' http://localhost:8000/oidc/dogs/` |
| `/api/*` | Backend | Backend handles auth directly | `curl -H 'X-API-Key: <key>' http://localhost:8000/api/dogs/` |

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Backend & Apps** |
| Django | 4.2.16 | Web framework |
| Django REST Framework | 3.15.2 | REST API |
| drf-spectacular | 0.27.2 | OpenAPI/Swagger documentation |
| Gunicorn | 23.0.0 | WSGI server |
| Whitenoise | 6.6.0 | Static file serving |
| **Infrastructure** |
| PostgreSQL | 16-alpine | Unified database server (all databases) |
| Kong | 3.4 (with OIDC) | API Gateway |
| Keycloak | 24.0 | Identity Provider (OIDC) |
| **Container & Orchestration** |
| Docker | 20.10+ | Containerization |
| Kubernetes | 1.28+ | Container orchestration |
| Helm | 3.0+ | Kubernetes package manager |
| Traefik | Latest | Kubernetes ingress controller |
| cert-manager | Latest | Automatic TLS certificates |

## Components

| Component | Docker Port | K8s Ingress | Description |
|-----------|-------------|-------------|-------------|
| **Dogcatcher API** | 5001 | dogcatcher.* | Django REST Framework API with Swagger docs |
| **Model Citizen App** | 5002 | citizen.* | Django citizen portal consuming API via Kong |
| **Certosaurus** | 8000 | certosaurus.* | Certificate authority management portal |
| **Kong Gateway** | 8000 | kong.* | API Gateway with multi-protocol authentication |
| **Kong Admin API** | 8001 | kong-admin.* | Kong configuration API |
| **Kong Manager** | 8002 | kong-manager.* | Kong web admin interface |
| **Keycloak** | 8090 | keycloak.* | Identity Provider for OIDC authentication |
| **PostgreSQL** | 5432 | Internal | Unified database server (3 databases) |

## Features

- **REST API** with Swagger/OpenAPI documentation (drf-spectacular)
- **Multi-protocol authentication**: Plain, API Key, JWT, mTLS, OIDC
- **Kong API Gateway** with OIDC plugin for OpenID Connect
- **Keycloak Identity Provider** for OIDC authentication
- **Certosaurus Certificate Management** - Web-based CA for generating server and client certificates
- **Health Endpoints** - All applications expose `/health/` for Kubernetes probes
- **Kubernetes-native deployment** with Helm charts
- **Auto-generated TLS certificates** via cert-manager and Let's Encrypt
- **Unified PostgreSQL** - Single database server hosting multiple databases
- **Production-ready** - Optimized Docker images with multi-stage builds
- **Django Admin interface** for database management

## Deployment Options

### Kubernetes Deployment (Recommended)

Deploy the complete application suite to Kubernetes using Helm.

#### Prerequisites

- Kubernetes cluster (1.28+) with:
  - Traefik ingress controller installed
  - cert-manager for automatic TLS certificates
  - Default storage class configured
- Helm 3.0+
- kubectl configured to access your cluster
- Wildcard DNS configured (or modify ingress hosts in values.yaml)

#### Quick Start - Helm Installation

```bash
# 1. Clone the repository
git clone https://github.com/Sunningdale-IT/apigw-poc.git
cd apigw-poc

# 2. (Optional) Build and push Docker images to your registry
cd helm-chart/apigw-demo
# Edit values.yaml to set your image registry
# Default uses docker.io/jimleitch/*

# Build images (if needed)
docker build --platform linux/amd64 -t <your-registry>/dogcatcher:latest -f ../../app/Dockerfile ../../app
docker build --platform linux/amd64 -t <your-registry>/citizen:latest -f ../../citizen-app/Dockerfile ../../citizen-app
docker build --platform linux/amd64 -t <your-registry>/certosaurus:latest -f ../../certosaurus/Dockerfile ../../certosaurus

# Push to registry
docker push <your-registry>/dogcatcher:latest
docker push <your-registry>/citizen:latest
docker push <your-registry>/certosaurus:latest

# 3. Configure your deployment
cp values.yaml my-values.yaml
# Edit my-values.yaml:
#   - Update global.domain to your domain
#   - Update image repositories if using custom registry
#   - Update ingress hosts
#   - Configure secrets and passwords

# 4. Create namespace
kubectl create namespace apigw-demo

# 5. Install with Helm
helm install apigw-demo . -f my-values.yaml -n apigw-demo

# 6. Monitor deployment
kubectl get pods -n apigw-demo -w

# 7. Check ingress and certificates
kubectl get ingress,certificates -n apigw-demo
```

#### Helm Chart Configuration

The Helm chart (`helm-chart/apigw-demo/`) includes:

- **Unified PostgreSQL StatefulSet** - Single database server with 3 databases (kong, dogcatcher, keycloak)
- **7 Application Deployments** - Dogcatcher (2 replicas), Kong (2 replicas), Citizen (2 replicas), Certosaurus, Keycloak
- **Health Checks** - All apps have liveness and readiness probes using `/health/` endpoints
- **TLS Ingresses** - Automatic certificate generation via cert-manager
- **PersistentVolumes** - For database data, uploads, and certificates
- **ConfigMaps & Secrets** - Externalized configuration

**Key Configuration Options** (values.yaml):

```yaml
global:
  domain: jim00.pd.test-rig.nl  # Your base domain
  storageClass: default         # Kubernetes storage class

postgres:
  enabled: true
  persistence:
    size: 20Gi                  # Storage for all databases
  databases:
    kong:
      name: kong
      username: kong
    dogcatcher:
      name: dogcatcher
      username: dogcatcher
    keycloak:
      name: keycloak
      username: keycloak

dogcatcher:
  replicaCount: 2
  image:
    repository: docker.io/jimleitch/dogcatcher
  ingress:
    host: dogcatcher.jim00.pd.test-rig.nl

kong:
  replicaCount: 2
  ingress:
    host: kong.jim00.pd.test-rig.nl

citizen:
  replicaCount: 2
  ingress:
    host: citizen.jim00.pd.test-rig.nl
```

#### Accessing Applications (Kubernetes)

After deployment, applications are available at:

- **Dogcatcher API**: https://dogcatcher.{your-domain}/api/docs/
- **Dogcatcher Admin**: https://dogcatcher.{your-domain}/admin/
- **Model Citizen**: https://citizen.{your-domain}/
- **Certosaurus**: https://certosaurus.{your-domain}/login/
- **Kong Proxy**: https://kong.{your-domain}/
- **Kong Admin**: https://kong-admin.{your-domain}/
- **Kong Manager**: https://kong-manager.{your-domain}/
- **Keycloak**: https://keycloak.{your-domain}/

#### Managing the Helm Release

```bash
# Upgrade deployment
helm upgrade apigw-demo . -f my-values.yaml -n apigw-demo

# Check status
helm status apigw-demo -n apigw-demo
helm list -n apigw-demo

# View logs
kubectl logs -f deployment/apigw-demo-dogcatcher -n apigw-demo
kubectl logs -f statefulset/apigw-demo-postgres -n apigw-demo

# Uninstall
helm uninstall apigw-demo -n apigw-demo
```

### Local Development (Docker Compose)

For local development and testing without Kubernetes:

### Local Development (Docker Compose)

For local development and testing without Kubernetes:

#### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

#### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Sunningdale-IT/apigw-poc.git
cd apigw-poc

# Copy environment template
cp .env.example .env

# Start all services (displays URLs when ready)
./scripts/start-local.sh

# Or use docker compose directly
docker compose up -d
```

The startup script will display all access URLs:

```
=============================================
   Dogcatcher Development Environment
=============================================

Dogcatcher API (Direct):
  Web UI:      http://localhost:5001/
  Swagger API: http://localhost:5001/api/docs/
  Admin:       http://localhost:5001/admin/  (user: admin, pass: admin123)

Model Citizen App:
  Web UI:      http://localhost:5002/
  Login:       http://localhost:5002/login/  (use: DEMO)

Kong API Gateway (port 8000):
  Public:      http://localhost:8000/public/dogs/  (no auth)
  API Key:     http://localhost:8000/apikey/dogs/  (X-API-Key header)
  JWT:         http://localhost:8000/jwt/dogs/     (Bearer token)
  mTLS:        https://localhost:8443/mtls/dogs/   (client cert)
  OIDC:        http://localhost:8000/oidc/dogs/    (OIDC token)
  Direct:      http://localhost:8000/api/dogs/     (backend auth)
  Admin API:   http://localhost:8001/

Kong Manager OSS:
  URL:         http://localhost:8002/  (no login required)

Keycloak Identity Provider:
  URL:         http://localhost:8090/
  Admin:       admin / admin

Nginx Proxy (port 8080):
  HTTP:        http://localhost:8080/
  HTTPS:       https://localhost:8443/
```

## Multi-Protocol Authentication

### 1. Plain (No Authentication)

Open access with no credentials required.

```bash
curl http://localhost:8000/public/dogs/
```

### 2. API Key Authentication

Kong validates the API key before forwarding requests.

```bash
# Using X-API-Key header
curl -H "X-API-Key: citizen-api-key-2026" http://localhost:8000/apikey/dogs/
```

**Pre-configured API Keys:**

| Consumer | API Key | Purpose |
|----------|---------|---------|
| model-citizen | `citizen-api-key-2026` | Model Citizen app |
| admin | `admin-api-key-2026` | Admin access |

### 3. JWT Authentication

Kong validates JWT signature and expiration.

```bash
# Generate a JWT token (requires PyJWT: pip install pyjwt)
TOKEN=$(python3 -c "
import jwt
import time
payload = {'iss': 'model-citizen-jwt', 'exp': int(time.time()) + 3600}
print(jwt.encode(payload, 'your-256-bit-secret-key-here-min32chars', 'HS256'))
")

# Use the token
curl -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/jwt/dogs/
```

**JWT Configuration:**

| Field | Value |
|-------|-------|
| Algorithm | HS256 |
| Issuer (iss) | `model-citizen-jwt` |
| Secret | `your-256-bit-secret-key-here-min32chars` |

### 4. mTLS Authentication

Requires client certificate for mutual TLS authentication.

```bash
# Generate certificates (see scripts/generate-mtls-certs.sh)
curl --cert certs/client.crt --key certs/client.key \
     --cacert certs/ca.crt \
     https://localhost:8443/mtls/dogs/
```

### 5. OIDC Authentication

OpenID Connect authentication via Keycloak.

**Setup Required:**
1. Access Keycloak at http://localhost:8090 (admin/admin)
2. Create a realm (e.g., `dogcatcher`)
3. Create a client for the API
4. Configure environment variables and re-run `configure-kong.sh`

```bash
# Set OIDC environment variables
export OIDC_DISCOVERY=http://keycloak:8080/realms/dogcatcher/.well-known/openid-configuration
export OIDC_CLIENT_ID=dogcatcher-api
export OIDC_CLIENT_SECRET=your-client-secret

# Re-configure Kong
./scripts/configure-kong.sh

# Use with access token from Keycloak
curl -H "Authorization: Bearer <oidc-access-token>" http://localhost:8000/oidc/dogs/
```

## API Documentation

### Swagger UI

Access the interactive API documentation at http://localhost:5001/api/docs/

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dogs/` | List all dogs |
| POST | `/api/dogs/` | Add a new dog |
| GET | `/api/dogs/{id}/` | Get dog by ID |
| DELETE | `/api/dogs/{id}/` | Delete a dog |
| GET | `/api/dogs/export/` | Export all data |
| GET | `/api/dogs/{id}/photo/` | Download dog photo |
| GET | `/api/schema/` | OpenAPI schema (JSON) |

## Project Structure

```
.
├── app/                              # Dogcatcher Django API
│   ├── manage.py                     # Django management script
│   ├── dogcatcher_project/           # Django project configuration
│   ├── dogs/                         # Dogs Django app
│   │   ├── views.py                  # Includes /api/health/ endpoint
│   │   └── urls.py
│   ├── templates/                    # HTML templates (including admin)
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── citizen-app/                      # Model Citizen Django app
│   ├── manage.py                     # Django management script
│   ├── citizen_project/              # Django project configuration
│   ├── services/                     # Services Django app
│   │   ├── views.py                  # Includes /health/ endpoint
│   │   └── urls.py
│   ├── templates/                    # HTML templates
│   ├── static/images/                # Static images
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── certosaurus/                        # Certificate Management Portal
│   ├── manage.py                     # Django management script
│   ├── certosaurus_project/            # Django project configuration
│   ├── certificates/                 # Certificates Django app
│   │   ├── views.py                  # Includes /health/ endpoint
│   │   ├── cert_utils.py             # Certificate generation utilities
│   │   └── models.py                 # CA, Server, Client cert models
│   ├── templates/                    # HTML templates
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── helm-chart/
│   └── apigw-demo/                   # Production Helm chart
│       ├── Chart.yaml                # Chart metadata
│       ├── values.yaml               # Default configuration
│       ├── templates/
│       │   ├── postgres-statefulset.yaml      # Unified PostgreSQL
│       │   ├── dogcatcher-deployment.yaml     # API deployment
│       │   ├── kong-deployment.yaml           # Kong gateway
│       │   ├── citizen-deployment.yaml        # Citizen app
│       │   ├── certosaurus-deployment.yaml      # Cert management
│       │   ├── keycloak-deployment.yaml       # Identity provider
│       │   ├── kong-migrations-job.yaml       # DB init job
│       │   ├── secrets.yaml                   # All secrets
│       │   └── *-ingress.yaml                 # TLS ingresses
│       ├── DEPLOYMENT.md             # Detailed deployment guide
│       └── README.md                 # Chart documentation
├── kong/                             # Custom Kong with OIDC
│   └── Dockerfile                    # Based on revomatico/docker-kong-oidc
├── scripts/                          # Automation scripts
│   ├── start-local.sh                # Start dev environment
│   ├── configure-kong.sh             # Configure Kong routes
│   ├── load-test-data.sh             # Load sample dogs
│   ├── deploy-k8s.sh                 # Kubernetes deployment helper
│   └── ...
├── docker-compose.yml                # Development compose file
├── K8S-DEPLOYMENT.md                 # Kubernetes deployment guide
├── .env.example                      # Environment template
└── README.md                         # This file
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ===========================================
# Dogcatcher API (Django)
# ===========================================
DOGCATCHER_SECRET_KEY=<random-32-char-hex>
DOGCATCHER_API_KEYS=key1,key2,key3
API_KEY_REQUIRED=true
DJANGO_DEBUG=false
ALLOWED_HOSTS=*

# ===========================================
# Kong API Gateway
# ===========================================
# Routes: /public, /apikey, /jwt, /mtls, /oidc, /api

# ===========================================
# OIDC Configuration (for /oidc route)
# ===========================================
# Configure these for OpenID Connect authentication
# OIDC_DISCOVERY=https://keycloak:8080/realms/dogcatcher/.well-known/openid-configuration
# OIDC_CLIENT_ID=dogcatcher-api
# OIDC_CLIENT_SECRET=your-client-secret

# ===========================================
# Model Citizen App (Django)
# ===========================================
CITIZEN_SECRET_KEY=<random-32-char-hex>
API_GATEWAY_URL=http://kong:8000/public
DOGCATCHER_PUBLIC_URL=http://localhost:8000/public
```

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 5001 | Dogcatcher | Direct API access |
| 5002 | Model Citizen | Citizen portal |
| 5432 | PostgreSQL | Database |
| 8000 | Kong Proxy | API Gateway (main) |
| 8001 | Kong Admin | Kong configuration API |
| 8002 | Kong Manager | Kong web UI |
| 8080 | Nginx | HTTP proxy |
| 8090 | Keycloak | Identity Provider |
| 8443 | Nginx | HTTPS/mTLS proxy |

## Django Admin

Access the Django admin interface at http://localhost:5001/admin/

**Default Credentials (Development Only):**
- Username: `admin`
- Password: `admin123`

The admin user is automatically created by the startup script.

## Kong Manager OSS

Kong Manager OSS is the official open-source admin GUI. Access it at http://localhost:8002/

**No login required** - provides direct access to manage Kong configuration.

### Kong Features

| Section | Description |
|---------|-------------|
| **Gateway Services** | Backend service configurations |
| **Routes** | URL routing and authentication |
| **Consumers** | API consumers and credentials |
| **Plugins** | Authentication, rate limiting, logging |
| **Upstreams** | Load balancing configuration |

## Keycloak Identity Provider

Keycloak provides OpenID Connect (OIDC) authentication. Access it at http://localhost:8090/

**Admin Credentials:**
- Username: `admin`
- Password: `admin`

### Keycloak Setup for OIDC

1. Login to Keycloak Admin Console
2. Create a new realm (e.g., `dogcatcher`)
3. Create a client:
   - Client ID: `dogcatcher-api`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
4. Get the client secret from Credentials tab
5. Configure Kong with the OIDC settings

## Loading Test Data

```bash
# Load 10 dogs with photos
./scripts/load-test-data.sh

# Load 5 dogs
./scripts/load-test-data.sh -n 5

# Clean up and reload
./scripts/load-test-data.sh --cleanup -n 10
```

## Development

### Common Commands

```bash
# Start all services
./scripts/start-local.sh

# Rebuild and start
./scripts/start-local.sh --build

# Configure Kong routes
./scripts/configure-kong.sh

# View logs
docker compose logs -f

# View specific service
docker compose logs -f kong

# Stop all services
docker compose down

# Run Django management commands
docker exec -it dogcatcher-web python manage.py migrate
docker exec -it dogcatcher-web python manage.py shell
```

### Database Migrations

**Kubernetes:**
```bash
# Get dogcatcher pod name
DOGCATCHER_POD=$(kubectl get pod -n apigw-demo -l app.kubernetes.io/component=dogcatcher -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- python manage.py makemigrations
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- python manage.py migrate

# Create superuser
kubectl exec -it $DOGCATCHER_POD -n apigw-demo -- python manage.py createsuperuser
```

**Docker Compose:**
```bash
docker exec -it dogcatcher-web python manage.py makemigrations
docker exec -it dogcatcher-web python manage.py migrate
```

## Unified PostgreSQL Database

The Helm chart uses a **single PostgreSQL StatefulSet** hosting three separate databases:

| Database | User | Used By | Purpose |
|----------|------|---------|---------|
| `kong` | kong | Kong Gateway | Gateway configuration and state |
| `dogcatcher` | dogcatcher | Dogcatcher API | Dog registry data |
| `keycloak` | keycloak | Keycloak | Identity and access management |

**Benefits:**
- Reduced resource usage (1 pod vs 3 pods)
- Simplified backup and recovery
- Single storage volume (20Gi by default)
- Automatic database initialization via init scripts
- Better for development and POC deployments

**Accessing the Database:**

```bash
# List all databases
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- psql -U postgres -c '\l'

# Connect to dogcatcher database
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- psql -U dogcatcher -d dogcatcher

# Connect to kong database
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- psql -U kong -d kong
```

## Docker Image Optimization

All application images use **multi-stage builds** for faster builds and smaller images:

- **Builder stage**: Compiles Python wheels with `--only-binary=:all:` flag
- **Runtime stage**: Slim Python image with pre-built wheels
- **Result**: ~95% faster builds (5-10s vs 90-150s), 40-50% smaller images

Build times comparison:
- Before: 90-150 seconds (with gcc compilation)
- After: 5-10 seconds (binary wheels only)

## Azure Deployment

Deploy to Azure Kubernetes Service:

```bash
# 1. Create AKS cluster (if needed)
az aks create \
  --resource-group apigw-poc-rg \
  --name apigw-cluster \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys

# 2. Get credentials
az aks get-credentials --resource-group apigw-poc-rg --name apigw-cluster

# 3. Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 4. Install Traefik (if not already installed)
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik -n kube-system

# 5. Deploy the application
cd helm-chart/apigw-demo
helm install apigw-demo . -f my-values.yaml -n apigw-demo
```

For VM-based deployment scripts:

```bash
./scripts/azure-create-vm.sh --install-app --dns-rg <your-dns-resource-group>
```

See the script help for all options:
```bash
./scripts/azure-create-vm.sh --help
```

## Security Notes

⚠️ **This is a proof-of-concept application.** For production:

1. **Change all default secrets** - Generate strong random keys for:
   - Django SECRET_KEY (Dogcatcher, Citizen, Certosaurus)
   - PostgreSQL passwords (postgres master, kong, dogcatcher, keycloak)
   - Keycloak admin password
   - Kong admin tokens
2. **Remove wildcard from ALLOWED_HOSTS** - Set specific domain names
3. **Use strong database passwords** - Update in values.yaml or use Kubernetes secrets
4. **Configure Keycloak properly** - Create proper realms, clients, and users
5. **Use Let's Encrypt certificates** - Already configured in cert-manager annotations
6. **Review RBAC permissions** - Apply least-privilege principles
7. **Enable network policies** - Restrict pod-to-pod communication
8. **Secure sensitive ConfigMaps/Secrets** - Use sealed-secrets or external secret managers

### Default Credentials (Development Only)

**Kubernetes Deployment:**
| Item | Value | Change In |
|------|-------|-----------|
| PostgreSQL Master | `postgres` / `postgres123` | values.yaml → postgres.env.password |
| Kong DB User | `kong` / `kong123` | values.yaml → postgres.databases.kong.password |
| Dogcatcher DB User | `dogcatcher` / `dogcatcher123` | values.yaml → postgres.databases.dogcatcher.password |
| Keycloak DB User | `keycloak` / `keycloak123` | values.yaml → postgres.databases.keycloak.password |
| Keycloak Admin | `admin` / `admin` | values.yaml → keycloak.env.adminPassword |
| Django Admin | Create via manage.py | Run createsuperuser in pod |

**Docker Compose:**
| Item | Value |
|------|-------|
| Django Admin | `admin` / `admin123` |
| Keycloak Admin | `admin` / `admin` |
| Kong API Key | `citizen-api-key-2026` |
| Database | `dogcatcher` / `dogcatcher123` |

## Troubleshooting

### Kubernetes Deployment

```bash
# Check all resources
kubectl get all,ingress,pvc,certificates -n apigw-demo

# Check pod status
kubectl get pods -n apigw-demo
kubectl describe pod <pod-name> -n apigw-demo

# View logs
kubectl logs -f deployment/apigw-demo-dogcatcher -n apigw-demo
kubectl logs -f statefulset/apigw-demo-postgres -n apigw-demo
kubectl logs -f deployment/apigw-demo-kong -n apigw-demo

# Check database
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- psql -U postgres -c '\l'

# Check certificates
kubectl get certificates -n apigw-demo
kubectl describe certificate dogcatcher-tls -n apigw-demo

# Check ingress
kubectl get ingress -n apigw-demo
kubectl describe ingress apigw-demo-dogcatcher -n apigw-demo

# Restart a deployment
kubectl rollout restart deployment/apigw-demo-dogcatcher -n apigw-demo

# Check Helm release
helm status apigw-demo -n apigw-demo
helm get values apigw-demo -n apigw-demo
```

### Common Issues

**Pods not starting:**
- Check PVC binding: `kubectl get pvc -n apigw-demo`
- Check image pull: `kubectl describe pod <pod> -n apigw-demo | grep -A 5 Events`
- Check resource limits: Ensure cluster has enough CPU/memory

**Database connection issues:**
- Verify postgres pod is running: `kubectl get pods -n apigw-demo -l app.kubernetes.io/component=postgres`
- Check database logs: `kubectl logs apigw-demo-postgres-0 -n apigw-demo`
- Verify init scripts ran: `kubectl logs apigw-demo-postgres-0 -n apigw-demo | grep "databases and users created"`

**TLS certificate issues:**
- Check cert-manager is running: `kubectl get pods -n cert-manager`
- Check certificate status: `kubectl describe certificate <cert-name> -n apigw-demo`
- Verify cluster issuer: `kubectl get clusterissuer`

**Health probe failures:**
- Check application logs for errors
- Verify `/health/` endpoint is accessible: `kubectl exec -it <pod> -n apigw-demo -- wget -qO- http://localhost:8000/health/`
- Check ALLOWED_HOSTS includes wildcard: Should include `*` for pod IP access

### Docker Compose

```bash
# Check Service Status
docker compose ps
docker compose logs kong
docker compose logs keycloak
```

### Test Authentication Routes

```bash
# Test all routes
curl http://localhost:8000/public/dogs/                     # Should work
curl http://localhost:8000/apikey/dogs/                     # Should fail (401)
curl -H "X-API-Key: citizen-api-key-2026" http://localhost:8000/apikey/dogs/  # Should work
curl http://localhost:8000/jwt/dogs/                        # Should fail (401)
curl http://localhost:8000/oidc/dogs/                       # Depends on config
```

### Kong Configuration

**Kubernetes:**
```bash
# Access Kong Admin API via port-forward
kubectl port-forward svc/apigw-demo-kong-admin 8001:8001 -n apigw-demo

# Or via ingress (if configured)
# https://kong-admin.{your-domain}/

# List routes
curl -s http://localhost:8001/routes | python3 -m json.tool

# List services
curl -s http://localhost:8001/services | python3 -m json.tool

# List plugins
curl -s http://localhost:8001/plugins | python3 -m json.tool
```

**Docker Compose:**
```bash
# List routes
curl -s http://localhost:8001/routes | python3 -m json.tool

# List services
curl -s http://localhost:8001/services | python3 -m json.tool

# List plugins
curl -s http://localhost:8001/plugins | python3 -m json.tool
```

## Additional Documentation

- **[K8S-DEPLOYMENT.md](K8S-DEPLOYMENT.md)** - Kubernetes deployment guide
- **[helm-chart/apigw-demo/DEPLOYMENT.md](helm-chart/apigw-demo/DEPLOYMENT.md)** - Detailed Helm chart documentation
- **[helm-chart/apigw-demo/README.md](helm-chart/apigw-demo/README.md)** - Chart configuration reference
- **[docs/KONG-DEPLOYMENT.md](docs/KONG-DEPLOYMENT.md)** - Kong configuration guide
- **[docs/MTLS-SETUP.md](docs/MTLS-SETUP.md)** - mTLS configuration
- **[docs/PROXY-MULTI-AUTH.md](docs/PROXY-MULTI-AUTH.md)** - Multi-auth setup

## License

This is a sample/POC application for demonstration purposes.

## Support

For issues or questions, please open an issue in the repository.
