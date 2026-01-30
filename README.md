# Dogcatcher API Gateway POC

A proof-of-concept demonstrating API Gateway patterns with a Flask-based dog catcher application. This project showcases multi-protocol authentication (API keys, mTLS, JWT, OIDC), reverse proxy configuration, and cloud deployment automation.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Model Citizen  │────▶│   Nginx Proxy   │────▶│  Dogcatcher API │
│      App        │     │  (Auth Gateway) │     │    (Flask)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               │                        ▼
                               │                ┌─────────────────┐
                               │                │   PostgreSQL    │
                               │                │    Database     │
                               ▼                └─────────────────┘
                        ┌─────────────────┐
                        │   Let's Encrypt │
                        │   (HTTPS certs) │
                        └─────────────────┘
```

## Components

| Component | Description |
|-----------|-------------|
| **Dogcatcher API** | Flask REST API with Swagger documentation for managing found dogs |
| **Model Citizen App** | Citizen portal that consumes the Dogcatcher API |
| **Nginx Proxy** | Reverse proxy supporting multiple auth protocols |
| **PostgreSQL** | Database for storing dog records |

## Features

- **REST API** with Swagger/OpenAPI documentation
- **Multi-protocol authentication**: Plain, API Key, mTLS, JWT, OIDC
- **Containerized deployment** with Docker Compose
- **Azure VM automation** with one-command deployment
- **Auto-generated SSL certificates** (self-signed or Let's Encrypt)
- **Automatic DNS updates** in Azure DNS
- **Scheduled resource cleanup** for test environments

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

# Start all services
docker compose up -d

# Access the application
# Swagger API: http://localhost:8080/api/docs
# Web UI: http://localhost:8080/
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
- **Swagger API**: https://dogcatcher.jim00.pd.test-rig.nl/api/docs
- **Health Check**: https://dogcatcher.jim00.pd.test-rig.nl/health

SSH to the VM:
```bash
ssh azureuser@dogcatcher.jim00.pd.test-rig.nl
```

## API Documentation

### Swagger UI

Access the interactive API documentation at `/api/docs` (e.g., https://dogcatcher.jim00.pd.test-rig.nl/api/docs)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dogs/` | List all dogs |
| POST | `/api/dogs/` | Add a new dog |
| GET | `/api/dogs/{id}` | Get dog by ID |
| DELETE | `/api/dogs/{id}` | Delete a dog |
| GET | `/api/dogs/export` | Export all data |
| GET | `/api/dogs/{id}/photo` | Download dog photo |

### Authentication

API requests require an API key header when `API_KEY_REQUIRED=true`:

```bash
curl -H "X-API-Key: demo-api-key-12345" https://dogcatcher.jim00.pd.test-rig.nl/plain/dogs/
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
# Plain access
curl -k https://dogcatcher.jim00.pd.test-rig.nl/plain/dogs/

# API key authentication
curl -k -H "X-API-Key: your-key" https://dogcatcher.jim00.pd.test-rig.nl/apikey/dogs/
```

## Project Structure

```
.
├── app/                          # Dogcatcher Flask API
│   ├── app.py                    # Main application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/                # HTML templates
├── citizen-app/                  # Model Citizen Flask app
│   ├── app.py
│   ├── Dockerfile
│   └── templates/
├── proxy/                        # Nginx reverse proxy
│   ├── Dockerfile
│   ├── nginx.conf                # Production config
│   ├── nginx-dev.conf            # Development config
│   ├── docker-entrypoint.sh
│   └── conf.d/
│       ├── proxy_routes.conf     # Auth route definitions
│       └── proxy_common.conf     # Common proxy settings
├── scripts/                      # Automation scripts
│   ├── azure-create-vm.sh        # Azure VM deployment
│   ├── setup-letsencrypt.sh      # Let's Encrypt setup
│   ├── generate-mtls-certs.sh    # mTLS certificate generation
│   ├── docker-build-push.sh      # Build and push images
│   └── start-local.sh            # Local development startup
├── helm-chart/                   # Kubernetes Helm charts
│   ├── model-citizen/
│   └── apigw-poc/
├── k8s-manifests/                # Kubernetes manifests
│   └── mtls/
├── docs/                         # Additional documentation
│   ├── KONG-DEPLOYMENT.md
│   ├── KONG-MTLS-SETUP.md
│   ├── LETSENCRYPT-SETUP.md
│   ├── MTLS-SETUP.md
│   └── PROXY-MULTI-AUTH.md
├── docker-compose.yml            # Development compose file
├── docker-compose.azure.yml      # Azure/production overrides
├── .env.example                  # Environment template
└── README.md
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Dogcatcher API
DOGCATCHER_SECRET_KEY=<random-32-char-hex>
DOGCATCHER_API_KEYS=key1,key2,key3
API_KEY_REQUIRED=true
FLASK_DEBUG=false

# Proxy
PROXY_MODE=prod              # 'dev' or 'prod'
ENABLE_HTTPS=true
ENABLE_MTLS=false
DOMAIN=dogcatcher.jim00.pd.test-rig.nl

# Model Citizen App
CITIZEN_SECRET_KEY=<random-32-char-hex>
DOGCATCHER_PUBLIC_URL=https://dogcatcher.jim00.pd.test-rig.nl
```

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 80 | Proxy | HTTP (redirects to HTTPS) |
| 443 | Proxy | HTTPS (main access) |
| 8443 | Proxy | mTLS (strict client cert) |
| 5001 | Dogcatcher | Direct API access (dev) |
| 5002 | Model Citizen | Direct app access (dev) |
| 5432 | PostgreSQL | Database |

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
# Start with development settings
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Stop all services
docker compose down
```

### Running Tests

```bash
# Load test data
./scripts/load-test-data.sh

# Test API endpoints
curl http://localhost:8080/health
curl -H "X-API-Key: demo-api-key-12345" http://localhost:8080/plain/dogs/
```

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
3. **Enable proper authentication** - Configure JWT/OIDC validators
4. **Use Let's Encrypt certificates** - Not self-signed certs
5. **Review firewall rules** - Restrict access as needed
6. **Enable audit logging** - Monitor access patterns
7. **Regular security updates** - Keep dependencies updated

### Default Credentials (Development Only)

| Item | Value |
|------|-------|
| API Key | `demo-api-key-12345` |
| Database Password | `dogcatcher123` |
| Database User | `dogcatcher` |

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
docker compose -f docker-compose.yml -f docker-compose.azure.yml logs proxy
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
