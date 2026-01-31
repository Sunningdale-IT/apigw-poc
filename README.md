# Dogcatcher API Gateway POC

A proof-of-concept demonstrating API Gateway patterns with a Django-based dog catcher application. This project showcases multi-protocol authentication (API keys, mTLS, JWT, OIDC), reverse proxy configuration with both Kong and Nginx, and cloud deployment automation.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Model Citizen  │────▶│  Kong Gateway   │────▶│  Dogcatcher API │
│  (Django App)   │     │  (API Gateway)  │     │  (Django REST)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
        ┌──────────────────────┤                        ▼
        │                      │                ┌─────────────────┐
        ▼                      │                │   PostgreSQL    │
┌─────────────────┐            │                │    Database     │
│   Kong DB       │            │                └─────────────────┘
│  (PostgreSQL)   │            ▼
└─────────────────┘     ┌─────────────────┐
                        │   Nginx Proxy   │
                        │   (Optional)    │
                        └─────────────────┘
```

### API Gateway Routes

Kong API Gateway provides multiple authentication methods via different URL paths:

| Route | Authentication | Example |
|-------|----------------|---------|
| `/public/*` | None (open access) | `curl http://localhost:8000/public/dogs/` |
| `/apikey/*` | Kong validates API key | `curl -H 'X-API-Key: citizen-api-key-2026' http://localhost:8000/apikey/dogs/` |
| `/api/*` | Backend handles auth | `curl -H 'X-API-Key: <key>' http://localhost:8000/api/dogs/` |

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 4.2.16 | Web framework |
| Django REST Framework | 3.15.2 | REST API |
| drf-spectacular | 0.27.2 | OpenAPI/Swagger documentation |
| PostgreSQL | 16 | Database |
| Gunicorn | 23.0.0 | WSGI server |
| Kong | 3.5 | API Gateway |
| Nginx | 1.25 | Reverse proxy (optional) |
| Docker | 20.10+ | Containerization |

## Components

| Component | Description |
|-----------|-------------|
| **Dogcatcher API** | Django REST Framework API with Swagger documentation for managing found dogs |
| **Model Citizen App** | Django citizen portal that consumes the Dogcatcher API via Kong |
| **Kong Gateway** | API Gateway with multiple authentication routes (public, API key, direct) |
| **Nginx Proxy** | Optional reverse proxy for mTLS and additional auth protocols |
| **PostgreSQL** | Database for storing dog records (separate DBs for app and Kong) |

## Features

- **REST API** with Swagger/OpenAPI documentation (drf-spectacular)
- **Multi-protocol authentication**: Plain, API Key, mTLS, JWT, OIDC
- **Containerized deployment** with Docker Compose
- **Azure VM automation** with one-command deployment
- **Auto-generated SSL certificates** (self-signed or Let's Encrypt)
- **Automatic DNS updates** in Azure DNS
- **Scheduled resource cleanup** for test environments
- **Django Admin interface** for database management

## Quick Start

### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- For Azure deployment: Azure CLI (`az`) installed and logged in

### Local Development

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
  Direct:      http://localhost:8000/api/dogs/     (backend auth)
  Admin API:   http://localhost:8001/

Kong Manager OSS:
  URL:         http://localhost:8002/  (no login required)

Nginx Proxy (port 8080):
  HTTP:        http://localhost:8080/
  HTTPS:       https://localhost:8443/
```

### Azure Cloud Deployment

Deploy the complete stack to an Azure VM with a single command:

```bash
# Full deployment with app installation and DNS update
./scripts/azure-create-vm.sh --install-app --dns-rg <your-dns-resource-group>

# Example:
./scripts/azure-create-vm.sh --install-app --dns-rg dns-resource-group
```

This will:
1. Create an Azure resource group and VM (2 vCPU, 4GB RAM, Ubuntu 22.04)
2. Install Docker and Docker Compose via cloud-init
3. Update DNS record: `dogcatcher.jim00.pd.test-rig.nl` → VM IP
4. Clone this repository and start the application
5. Generate SSL certificates for HTTPS
6. Schedule automatic deletion at 19:00 UTC daily

#### Azure VM Script Options

```bash
./scripts/azure-create-vm.sh [OPTIONS]

Options:
  -n, --name            VM name (default: dogcatcher-vm)
  -g, --resource-group  Resource group name (default: dogcatcher-rg)
  -l, --location        Azure region (default: uksouth)
  -s, --size            VM size (default: Standard_B2s)
  --ssh-key             Path to SSH public key
  --admin-user          Admin username (default: azureuser)
  --dns-rg GROUP        Resource group containing Azure DNS zone
  --no-dns              Skip DNS record update
  --install-app         Clone and start app after VM creation
  --auto-delete TIME    Schedule daily deletion (default: 19:00 UTC)
  --no-auto-delete      Disable auto-deletion
  --open-http           Also open ports 8080 and 8443
  --dry-run             Show commands without executing
  -h, --help            Show help message
```

#### After Deployment

Access the application at:
- **Web UI**: https://dogcatcher.jim00.pd.test-rig.nl/
- **Swagger API**: https://dogcatcher.jim00.pd.test-rig.nl/api/docs/
- **Health Check**: https://dogcatcher.jim00.pd.test-rig.nl/health

SSH to the VM:
```bash
ssh azureuser@dogcatcher.jim00.pd.test-rig.nl
```

## API Documentation

### Swagger UI

Access the interactive API documentation at `/api/docs/` (e.g., http://localhost:5001/api/docs/)

The API uses drf-spectacular for OpenAPI 3.0 schema generation with full Swagger UI support.

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

### Authentication

API requests require an API key header when `API_KEY_REQUIRED=true`:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5001/api/dogs/
```

## Multi-Protocol Authentication Routes

The Nginx proxy supports different authentication methods via URL paths:

| Route | Auth Method | Description |
|-------|-------------|-------------|
| `/plain/*` | None | Direct access (for testing) |
| `/apikey/*` | API Key | Requires `X-API-Key` header |
| `/mtls/*` | mTLS | Requires client certificate |
| `/jwt/*` | JWT | Requires valid JWT token |
| `/oidc/*` | OIDC | OAuth2/OpenID Connect |

Example:
```bash
# Plain access (API key still required by Dogcatcher API)
curl http://localhost:8080/plain/api/dogs/

# API key authentication via proxy
curl -H "X-API-Key: your-key" http://localhost:8080/apikey/api/dogs/
```

## Project Structure

```
.
├── app/                              # Dogcatcher Django API
│   ├── manage.py                     # Django management script
│   ├── dogcatcher_project/           # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py               # Django settings
│   │   ├── urls.py                   # Root URL configuration
│   │   └── wsgi.py                   # WSGI application
│   ├── dogs/                         # Dogs Django app
│   │   ├── __init__.py
│   │   ├── admin.py                  # Django admin configuration
│   │   ├── apps.py                   # App configuration
│   │   ├── models.py                 # Dog model (Django ORM)
│   │   ├── permissions.py            # API key permission class
│   │   ├── serializers.py            # DRF serializers
│   │   ├── urls.py                   # API URL routes
│   │   ├── views.py                  # API ViewSets
│   │   ├── web_urls.py               # Web UI URL routes
│   │   ├── web_views.py              # Web UI views
│   │   └── migrations/               # Database migrations
│   ├── templates/                    # HTML templates
│   ├── static/                       # Static files
│   ├── Dockerfile
│   └── requirements.txt
├── citizen-app/                      # Model Citizen Django app
│   ├── manage.py                     # Django management script
│   ├── citizen_project/              # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py               # Django settings
│   │   ├── urls.py                   # Root URL configuration
│   │   └── wsgi.py                   # WSGI application
│   ├── services/                     # Services Django app
│   │   ├── __init__.py
│   │   ├── apps.py                   # App configuration
│   │   ├── decorators.py             # Login required decorator
│   │   ├── urls.py                   # URL routes
│   │   └── views.py                  # View functions
│   ├── templates/                    # HTML templates
│   ├── static/                       # Static files
│   ├── Dockerfile
│   └── requirements.txt
├── proxy/                            # Nginx reverse proxy
│   ├── Dockerfile
│   ├── nginx.conf                    # Production config
│   ├── nginx-dev.conf                # Development config
│   ├── docker-entrypoint.sh
│   └── conf.d/
│       ├── proxy_routes.conf         # Auth route definitions
│       └── proxy_common.conf         # Common proxy settings
├── scripts/                          # Automation scripts
│   ├── azure-create-vm.sh            # Azure VM deployment
│   ├── setup-letsencrypt.sh          # Let's Encrypt setup
│   ├── generate-mtls-certs.sh        # mTLS certificate generation
│   └── docker-build-push.sh          # Build and push images
├── helm-chart/                       # Kubernetes Helm charts
│   ├── model-citizen/
│   └── apigw-poc/
├── k8s-manifests/                    # Kubernetes manifests
│   └── mtls/
├── docs/                             # Additional documentation
│   ├── KONG-DEPLOYMENT.md
│   ├── KONG-MTLS-SETUP.md
│   ├── LETSENCRYPT-SETUP.md
│   ├── MTLS-SETUP.md
│   └── PROXY-MULTI-AUTH.md
├── docker-compose.yml                # Development compose file
├── docker-compose.azure.yml          # Azure/production overrides
├── .env.example                      # Environment template
└── README.md
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Dogcatcher API (Django)
DOGCATCHER_SECRET_KEY=<random-32-char-hex>
DOGCATCHER_API_KEYS=key1,key2,key3
API_KEY_REQUIRED=true
DJANGO_DEBUG=false
ALLOWED_HOSTS=*

# Database
POSTGRES_PASSWORD=dogcatcher123

# Proxy
PROXY_MODE=prod              # 'dev' or 'prod'
ENABLE_HTTPS=true
ENABLE_MTLS=false
DOMAIN=dogcatcher.jim00.pd.test-rig.nl

# Model Citizen App (Django)
CITIZEN_SECRET_KEY=<random-32-char-hex>
API_GATEWAY_URL=http://proxy/plain
DOGCATCHER_PUBLIC_URL=https://dogcatcher.jim00.pd.test-rig.nl
```

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 80 | Proxy | HTTP (redirects to HTTPS in prod) |
| 443 | Proxy | HTTPS (main access) |
| 8080 | Proxy (dev) | HTTP development access |
| 8443 | Proxy | HTTPS development |
| 8444 | Proxy | mTLS (strict client cert) |
| 5001 | Dogcatcher | Direct API access (dev) |
| 5002 | Model Citizen | Direct app access (dev) |
| 5432 | PostgreSQL | Database |

## Django Admin

Access the Django admin interface for database management at http://localhost:5001/admin/

**Default Credentials (Development Only):**
- Username: `admin`
- Password: `admin123`

To create the default admin user:

```bash
docker exec -it dogcatcher-web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Admin user created')
else:
    print('Admin user already exists')
"
```

Or create a custom superuser:

```bash
docker exec -it dogcatcher-web python manage.py createsuperuser
```

## Kong Manager OSS

Kong Manager OSS is the official open-source admin GUI included with Kong Gateway 3.x. Access it at http://localhost:8002/

**No login required** - Kong Manager OSS provides direct access to manage your Kong Gateway configuration.

### Features

Kong Manager OSS provides a web interface to manage:

| Section | Description |
|---------|-------------|
| **Overview** | Kong Gateway info, version, ports, datastore details |
| **Gateway Services** | Backend service configurations |
| **Routes** | URL routing rules and path matching |
| **Consumers** | API consumers and their credentials |
| **Plugins** | Authentication, rate limiting, logging plugins |
| **Upstreams** | Load balancing and health check configuration |
| **Certificates** | TLS/SSL certificate management |
| **Vaults** | Secret management |

### Kong API Keys

Pre-configured API keys for the `/apikey/*` route:

| Consumer | API Key | Purpose |
|----------|---------|---------|
| model-citizen | `citizen-api-key-2026` | Model Citizen app |
| admin | `admin-api-key-2026` | Admin access |

Test with:
```bash
curl -H "X-API-Key: citizen-api-key-2026" http://localhost:8000/apikey/dogs/
```

## Let's Encrypt SSL Certificates

For production, obtain trusted SSL certificates:

```bash
# SSH to the VM
ssh azureuser@dogcatcher.jim00.pd.test-rig.nl

# Run Let's Encrypt setup
cd /opt/dogcatcher/apigw-poc
./scripts/setup-letsencrypt.sh --domain dogcatcher.jim00.pd.test-rig.nl --email your@email.com
```

## Development

### Local Development

```bash
# Start with development settings (displays URLs)
./scripts/start-local.sh

# Start and rebuild containers
./scripts/start-local.sh --build

# Start and follow logs
./scripts/start-local.sh --logs

# Or use docker compose directly
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f web
docker compose logs -f citizen

# Rebuild after code changes
docker compose up -d --build

# Run Django management commands
docker exec -it dogcatcher-web python manage.py migrate
docker exec -it dogcatcher-web python manage.py shell

# Stop all services
docker compose down
```

### Database Migrations

```bash
# Create new migrations
docker exec -it dogcatcher-web python manage.py makemigrations

# Apply migrations
docker exec -it dogcatcher-web python manage.py migrate

# Show migration status
docker exec -it dogcatcher-web python manage.py showmigrations
```

### Running Tests

```bash
# Test API endpoints
curl http://localhost:5001/api/dogs/
curl -H "X-API-Key: your-api-key-here" http://localhost:5001/api/dogs/

# Test health endpoint
curl http://localhost:8080/health
```

### Loading Test Data

The `load-test-data.sh` script populates the application with sample dog entries including photos downloaded from the [Dog CEO API](https://dog.ceo/dog-api/).

```bash
# Load 10 dogs with default settings (reads API key from .env)
./scripts/load-test-data.sh

# Load 5 dogs
./scripts/load-test-data.sh -n 5

# Load 15 dogs with a specific API key
./scripts/load-test-data.sh -k your-api-key -n 15

# Clean up existing dogs before loading new ones
./scripts/load-test-data.sh --cleanup -n 10

# Load data to a remote deployment
./scripts/load-test-data.sh -u https://dogcatcher.jim00.pd.test-rig.nl -n 10
```

**Options:**

| Option | Description |
|--------|-------------|
| `-u, --url URL` | Base URL for dogcatcher (default: http://localhost:5001) |
| `-k, --api-key KEY` | API key for authentication (reads from .env if not provided) |
| `-n, --count N` | Number of dogs to create (default: 10, max: 20) |
| `-c, --cleanup` | Remove all existing dogs before loading |
| `-h, --help` | Show help message |

**Requirements:** `curl` and `jq` must be installed.

The script creates realistic test data including:
- 20 unique dog names and breeds
- Random location coordinates (NYC area)
- Descriptive comments for each dog
- Photos downloaded from the Dog CEO API

## Azure Resource Management

### Check VM Status

```bash
az vm show --resource-group dogcatcher-rg --name dogcatcher-vm --show-details -o table
```

### Manual Cleanup

```bash
# Delete the entire resource group (VM, networking, automation)
az group delete --name dogcatcher-rg --yes --no-wait
```

### Update Running VM

```bash
# SSH and pull latest code
ssh azureuser@dogcatcher.jim00.pd.test-rig.nl
cd /opt/dogcatcher/apigw-poc
git pull
docker compose -f docker-compose.yml -f docker-compose.azure.yml up -d --build
```

## Kubernetes Deployment

For Kubernetes deployment, see:
- `helm-chart/model-citizen/` - Helm chart for Model Citizen app
- `docs/KONG-DEPLOYMENT.md` - Kong API Gateway setup
- `docs/KONG-MTLS-SETUP.md` - mTLS configuration with Kong

## Security Notes

⚠️ **This is a proof-of-concept application.** For production use:

1. **Change all default secrets** - Generate strong random keys
2. **Use strong database passwords** - Not the default credentials
3. **Set ALLOWED_HOSTS properly** - Don't use `*` in production
4. **Enable proper authentication** - Configure JWT/OIDC validators
5. **Use Let's Encrypt certificates** - Not self-signed certs
6. **Review firewall rules** - Restrict access as needed
7. **Enable audit logging** - Monitor access patterns
8. **Regular security updates** - Keep dependencies updated

### Default Credentials (Development Only)

| Item | Value |
|------|-------|
| Django Admin Username | `admin` |
| Django Admin Password | `admin123` |
| API Key | `your-api-key-here` (from .env) |
| Database Password | `dogcatcher123` |
| Database User | `dogcatcher` |
| Database Name | `dogcatcher` |

## Troubleshooting

### VM Connection Issues

```bash
# Check VM is running
az vm show -g dogcatcher-rg -n dogcatcher-vm --show-details --query powerState

# Check public IP
az vm show -g dogcatcher-rg -n dogcatcher-vm --show-details --query publicIps -o tsv
```

### Container Issues

```bash
# SSH to VM and check containers
ssh azureuser@dogcatcher.jim00.pd.test-rig.nl
docker compose -f docker-compose.yml -f docker-compose.azure.yml ps
docker compose -f docker-compose.yml -f docker-compose.azure.yml logs web
docker compose -f docker-compose.yml -f docker-compose.azure.yml logs citizen
```

### Database Issues

```bash
# Check database connection
docker exec -it dogcatcher-web python manage.py dbshell

# Check migrations
docker exec -it dogcatcher-web python manage.py showmigrations
```

### DNS Not Resolving

```bash
# Check DNS record
nslookup dogcatcher.jim00.pd.test-rig.nl

# Verify Azure DNS record
az network dns record-set a show -g <dns-rg> -z jim00.pd.test-rig.nl -n dogcatcher
```

## License

This is a sample/POC application for demonstration purposes.

## Support

For issues or questions, please open an issue in the repository.
