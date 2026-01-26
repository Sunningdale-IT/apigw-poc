# Kong API Gateway - Proof of Concept

This repository contains a proof of concept demonstrating the use of Kong API Gateway with two sample microservices (Producer and Consumer) deployed on Kubernetes.

## 📋 Overview

This PoC demonstrates how Kong API Gateway simplifies the integration between microservices by:
- **Centralized Routing**: All API traffic flows through Kong, eliminating the need for services to know each other's locations
- **Service Discovery**: Services communicate via Kong routes instead of direct service URLs
- **Namespace Isolation**: Each service runs in its own Kubernetes namespace, promoting security and organization
- **API Management**: Kong provides a single point for managing, monitoring, and securing APIs

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                   │
│                                                           │
│  ┌───────────────┐      ┌───────────────┐               │
│  │   Namespace:  │      │   Namespace:  │               │
│  │   producer    │      │     kong      │               │
│  │               │      │               │               │
│  │  ┌─────────┐  │      │  ┌─────────┐  │               │
│  │  │Producer │  │◄─────┼──│  Kong   │  │               │
│  │  │  App    │  │      │  │ Gateway │  │               │
│  │  │         │  │      │  │         │  │               │
│  │  │ Admin:  │  │      │  └─────────┘  │               │
│  │  │ /admin  │  │      │  Routes:       │               │
│  │  └─────────┘  │      │  /producer     │               │
│  │   Port: 80    │      │  /consumer     │               │
│  └───────────────┘      └───────────────┘               │
│                                 │                         │
│                                 │                         │
│  ┌───────────────┐              │                        │
│  │   Namespace:  │              │                        │
│  │   consumer    │              │                        │
│  │               │              │                        │
│  │  ┌─────────┐  │              │                        │
│  │  │Consumer │  │◄─────────────┘                        │
│  │  │  App    │  │                                       │
│  │  │         │  │                                       │
│  │  │ Admin:  │  │                                       │
│  │  │ /admin  │  │                                       │
│  │  └─────────┘  │                                       │
│  │   Port: 80    │                                       │
│  └───────────────┘                                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **Producer Application** (Namespace: `producer`)
   - Django-based REST API that generates data
   - Custom admin dashboard at `/admin-dashboard` for monitoring
   - Built-in Django admin at `/admin` for database management
   - Endpoints:
     - `GET /api/data` - Get all produced data
     - `GET /api/data/latest` - Get latest data item
     - `POST /api/produce` - Generate new data
     - `GET /health` - Health check

2. **Consumer Application** (Namespace: `consumer`)
   - Django-based REST API that consumes data from Producer
   - Custom admin dashboard at `/admin-dashboard` for monitoring
   - Built-in Django admin at `/admin` for database management
   - Communicates with Producer **only through Kong Gateway**
   - Endpoints:
     - `GET /api/consume` - Fetch data from Producer via Kong
     - `POST /api/trigger-produce` - Trigger Producer via Kong
     - `GET /api/consumed` - View consumed data
     - `GET /health` - Health check

3. **Kong API Gateway** (Namespace: `kong`)
   - Routes requests to Producer and Consumer services
   - Provides centralized API management
   - Exposes services via NodePort (30080 for proxy, 30081 for admin)
   - Routes:
     - `/producer/*` → Producer service
     - `/consumer/*` → Consumer service

## 🚀 Quick Start

### Prerequisites

- Azure Kubernetes Service (AKS) cluster with cert-manager installed
- Azure Container Registry (ACR) or Docker Hub account
- Docker
- kubectl configured to access your AKS cluster
- curl and jq (optional, for testing)

### Deployment Steps

```bash
# 1. Build Docker images
./scripts/build-images.sh

# 2. Tag and push images to your container registry
# For Azure Container Registry:
docker tag producer-app:latest <your-acr>.azurecr.io/producer-app:latest
docker tag consumer-app:latest <your-acr>.azurecr.io/consumer-app:latest
docker push <your-acr>.azurecr.io/producer-app:latest
docker push <your-acr>.azurecr.io/consumer-app:latest

# 3. Update image references in deployment files
# Edit k8s-manifests/producer/01-deployment.yaml
# Edit k8s-manifests/consumer/01-deployment.yaml
# Update image: producer-app:latest to image: <your-acr>.azurecr.io/producer-app:latest
# Update image: consumer-app:latest to image: <your-acr>.azurecr.io/consumer-app:latest

# 4. Deploy to AKS
./scripts/deploy.sh

# 5. Wait for external IPs to be assigned
kubectl get ingress -A

# 6. Configure DNS records
# Point the following domains to the ingress external IPs:
# - kong.jim00.pd.test-rig.nl
# - producer.jim00.pd.test-rig.nl
# - consumer.jim00.pd.test-rig.nl

# 7. Test the setup (after DNS propagation)
./scripts/test-api.sh
```

### Note on cert-manager

This deployment assumes that cert-manager is already installed on your AKS cluster with a ClusterIssuer named `letsencrypt-prod`. The ingress configurations will automatically request TLS certificates from Let's Encrypt.

If you need to install cert-manager, refer to the [cert-manager documentation](https://cert-manager.io/docs/installation/)

## 📊 Accessing the Applications

All services are accessible via HTTPS using external domain names:

- **Kong Gateway**: `https://kong.jim00.pd.test-rig.nl`
- **Producer Custom Admin**: `https://producer.jim00.pd.test-rig.nl/admin-dashboard`
- **Producer Django Admin**: `https://producer.jim00.pd.test-rig.nl/admin`
- **Consumer Custom Admin**: `https://consumer.jim00.pd.test-rig.nl/admin-dashboard`
- **Consumer Django Admin**: `https://consumer.jim00.pd.test-rig.nl/admin`

### Via Kong Gateway Routes

You can also access services through Kong:

- **Producer via Kong**: `https://kong.jim00.pd.test-rig.nl/producer/*`
- **Consumer via Kong**: `https://kong.jim00.pd.test-rig.nl/consumer/*`

## 🧪 Testing the Setup

### Manual Testing

```bash
# Check health of Producer
curl https://producer.jim00.pd.test-rig.nl/health

# Check health of Consumer
curl https://consumer.jim00.pd.test-rig.nl/health

# Get data from Producer
curl https://producer.jim00.pd.test-rig.nl/api/data

# Trigger Consumer to fetch from Producer (via Kong)
curl https://consumer.jim00.pd.test-rig.nl/api/consume

# Trigger Producer to generate new data (from Consumer via Kong)
curl -X POST https://consumer.jim00.pd.test-rig.nl/api/trigger-produce

# Test via Kong Gateway routes
curl https://kong.jim00.pd.test-rig.nl/producer/health
curl https://kong.jim00.pd.test-rig.nl/consumer/health
```

### Automated Testing

```bash
# Run the test script
./scripts/test-api.sh
```

## 🎯 How Kong Makes Integration Easier

This PoC demonstrates several key benefits of using an API Gateway:

### 1. **Service Decoupling**
- Consumer doesn't need to know the Producer's actual location
- Services communicate through Kong routes (e.g., `/producer`) instead of direct URLs
- Services can be moved, scaled, or replaced without changing consumer code

### 2. **Centralized Configuration**
- All routing rules are defined in one place (Kong ConfigMap)
- Easy to add new routes, services, or modify existing ones
- Single source of truth for API endpoints

### 3. **Namespace Isolation**
- Each service runs in its own namespace for security
- Kong bridges communication across namespaces
- Services are isolated but can still communicate securely

### 4. **Future Extensibility**
Kong can easily be extended to add:
- Authentication and authorization
- Rate limiting
- Request/response transformation
- Logging and monitoring
- Load balancing
- Circuit breakers
- API versioning

### 5. **Admin Interfaces**
Both applications include dual admin interfaces:
- **Custom Admin Dashboard** (`/admin-dashboard`): Simple monitoring interface showing:
  - Request statistics
  - Data flow
  - Service health
  - Real-time monitoring (auto-refresh every 5 seconds)
  - API usage patterns
- **Django Admin** (`/admin`): Full-featured Django administration interface for:
  - Database management
  - Data inspection and editing
  - User management
  - Advanced filtering and search

## 📁 Project Structure

```
.
├── producer-app/           # Producer microservice (Django)
│   ├── producerapp/       # Django project configuration
│   │   ├── settings.py    # Django settings
│   │   ├── urls.py        # URL routing
│   │   └── wsgi.py        # WSGI application
│   ├── producer/          # Django app
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   ├── admin.py       # Django admin configuration
│   │   ├── serializers.py # DRF serializers
│   │   └── templates/     # HTML templates
│   ├── manage.py          # Django management script
│   ├── Dockerfile         # Docker image definition
│   └── requirements.txt   # Python dependencies
├── consumer-app/          # Consumer microservice (Django)
│   ├── consumerapp/       # Django project configuration
│   │   ├── settings.py    # Django settings
│   │   ├── urls.py        # URL routing
│   │   └── wsgi.py        # WSGI application
│   ├── consumer/          # Django app
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   ├── admin.py       # Django admin configuration
│   │   ├── serializers.py # DRF serializers
│   │   └── templates/     # HTML templates
│   ├── manage.py          # Django management script
│   ├── Dockerfile         # Docker image definition
│   └── requirements.txt   # Python dependencies
├── k8s-manifests/        # Kubernetes manifests
│   ├── kong/            # Kong Gateway configuration
│   │   ├── 00-namespace.yaml
│   │   ├── 01-configmap.yaml
│   │   ├── 02-deployment.yaml
│   │   ├── 03-service.yaml
│   │   └── 04-ingress.yaml
│   ├── producer/        # Producer service manifests
│   │   ├── 00-namespace.yaml
│   │   ├── 01-deployment.yaml
│   │   ├── 02-service.yaml
│   │   └── 03-ingress.yaml
│   └── consumer/        # Consumer service manifests
│       ├── 00-namespace.yaml
│       ├── 01-deployment.yaml
│       ├── 02-service.yaml
│       └── 03-ingress.yaml
├── scripts/              # Utility scripts
│   ├── build-images.sh   # Build Docker images
│   ├── deploy.sh         # Deploy to Kubernetes
│   ├── test-api.sh       # Test the deployment
│   ├── status.sh         # Check deployment status
│   └── cleanup.sh        # Remove all resources
└── README.md            # This file
```

## 🔧 Configuration

### Ingress and External Access

The deployment uses Kubernetes Ingress with cert-manager for external HTTPS access:

**External URLs:**
- Kong Gateway: `https://kong.jim00.pd.test-rig.nl`
- Producer Service: `https://producer.jim00.pd.test-rig.nl`
- Consumer Service: `https://consumer.jim00.pd.test-rig.nl`

Each service has its own ingress configuration in `k8s-manifests/*/03-ingress.yaml` that:
- Configures TLS/SSL using cert-manager
- Requests certificates from Let's Encrypt
- Routes traffic to the appropriate service

**DNS Configuration:**
You need to create DNS A records pointing to your ingress controller's external IP:
```bash
# Get the ingress external IP
kubectl get ingress -A

# Create DNS records pointing to this IP:
# - kong.jim00.pd.test-rig.nl
# - producer.jim00.pd.test-rig.nl  
# - consumer.jim00.pd.test-rig.nl
```

### Kong Routes

Routes are configured in `k8s-manifests/kong/01-configmap.yaml`:

```yaml
services:
- name: producer-service
  url: http://producer-service.producer:80
  routes:
  - name: producer-route
    paths:
    - /producer
    strip_path: true

- name: consumer-service
  url: http://consumer-service.consumer:80
  routes:
  - name: consumer-route
    paths:
    - /consumer
    strip_path: true
```

### Environment Variables

**Consumer Application:**
- `PRODUCER_API_URL`: Kong Gateway URL for Producer service (default: `http://kong-proxy.kong:8000/producer`)
- `PORT`: Application port (default: `5001`)

**Producer Application:**
- `PORT`: Application port (default: `5000`)

## 📊 Monitoring

### Check Deployment Status

```bash
./scripts/status.sh
```

### View Logs

```bash
# Kong logs
kubectl logs -n kong -l app=kong-proxy -f

# Producer logs
kubectl logs -n producer -l app=producer -f

# Consumer logs
kubectl logs -n consumer -l app=consumer -f
```

### Check Services

```bash
kubectl get all -n kong
kubectl get all -n producer
kubectl get all -n consumer
```

## 🧹 Cleanup

To remove all deployed resources:

```bash
./scripts/cleanup.sh
```

## 🎓 Learning Outcomes

After working with this PoC, you will understand:

1. How Kong API Gateway routes traffic between microservices
2. How to configure Kong using declarative configuration
3. Benefits of namespace isolation in Kubernetes
4. How services can communicate through an API gateway
5. How to monitor microservices with admin interfaces
6. How API gateways simplify microservice architecture

## 🔜 Next Steps

To further explore Kong's capabilities, you can:

1. Add authentication plugins (JWT, OAuth2, API Keys)
2. Implement rate limiting
3. Add request/response logging
4. Configure load balancing for multiple replicas
5. Set up HTTPS/TLS termination
6. Add custom plugins
7. Integrate with monitoring tools (Prometheus, Grafana)

## 📝 License

This is a proof of concept for educational purposes.

## 🤝 Contributing

This is a demonstration project. Feel free to fork and extend it for your own learning.