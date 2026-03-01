# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A proof-of-concept demonstrating API Gateway patterns. The primary showcase is multi-protocol authentication (Plain, API Key, JWT, mTLS, OIDC) flowing through Kong Gateway to a Django REST backend, with a consumer web portal (Model Citizen) calling multiple downstream microservices.

## Local Development

```bash
# Copy and edit environment file before first run
cp .env.example .env

# Start all services
docker-compose up

# Start specific service(s)
docker-compose up web citizen

# Run Django management commands inside a container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec citizen python manage.py shell
```

## Building and Pushing Images

```bash
# Build all images (linux/amd64 cross-platform via buildx)
./scripts/docker-build-push.sh -u <dockerhub-username>

# Build and push specific service(s)
./scripts/docker-build-push.sh -u <dockerhub-username> -p --app dogcatcher,citizen

# Valid app names: dogcatcher, citizen, certosaur, kong, moviezzz, free-parking, good-behaviour, park-runs
```

## Kubernetes Deployment

The Helm chart is at `helm-chart/apigw-demo/`. The target cluster uses Traefik ingress + cert-manager with wildcard DNS `*.jim00.pd.test-rig.nl`.

```bash
# Deploy
helm install apigw-demo helm-chart/apigw-demo -f helm-chart/apigw-demo/my-values.yaml -n apigw-demo --create-namespace

# Upgrade
helm upgrade apigw-demo helm-chart/apigw-demo -f helm-chart/apigw-demo/my-values.yaml -n apigw-demo

# Monitor
kubectl get pods -n apigw-demo -w
kubectl get all,ingress,pvc -n apigw-demo
```

## Architecture

```
Internet → Kong Gateway (port 8000) → Dogcatcher API (port 5000)
               ↓ mTLS (port 5443)
           Good Behaviour (behaviour records, mTLS)
               ↑
Model Citizen portal (port 5002)
    ├── calls Kong → Dogcatcher (found dogs), Good Behaviour (behaviour check)
    ├── calls Moviezzz directly
    ├── calls Free Parking directly
    └── calls Park Runs directly

Certosaur (port 5003) — certificate management UI
Keycloak (port 8090) — OIDC identity provider
Nginx Proxy (port 8080/8443/8444) — multi-protocol routing
```

### Services and Their Roles

| Service | Dir | Port | DB | Notes |
|---------|-----|------|----|-------|
| Dogcatcher API | `app/` | 5001 (direct) | PostgreSQL | Django REST, photo uploads, DRF Spectacular/Swagger |
| Model Citizen | `citizen-app/` | 5002 | SQLite | Django web portal, mock citizens (CIT001/CIT002/CIT003/DEMO) |
| Certosaur | `certosaur/` | 5003 | SQLite | Django, issues CA/server/client certs via UI |
| Good Behaviour | `good-behaviour/` | 5000/5443 | PostgreSQL | Django, behaviour records; dual-port when mTLS enabled |
| Free Parking | `free-parking/` | — | SQLite | Django, parking spots API |
| Moviezzz | `moviezzz/` | — | SQLite | Django, cinema listings API |
| Park Runs | `park-runs/` | — | SQLite | Django, park run events API |
| Kong | `kong/` | 8000/8001/8002 | PostgreSQL | Custom image with `oidc` plugin added to `bundled` |

### Kong Authentication Routes

Kong exposes these routes to the Dogcatcher API backend:

- `/public` — No auth; injects `X-Auth-Mode: public`
- `/apikey` — API key via `X-API-Key`; injects `X-Auth-Verified: true`
- `/jwt` — JWT token auth
- `/mtls` — Mutual TLS (client certificate)
- `/oidc` — OpenID Connect via Keycloak
- `/api` — Direct passthrough; backend enforces auth

### Dogcatcher Auth Logic (`app/dogs/permissions.py`)

The `APIKeyPermission` class checks in order:
1. `API_KEY_REQUIRED=false` → allow all
2. `X-Auth-Verified: true` header → allow (set by Kong after upstream auth)
3. `X-Auth-Mode: public` header → allow (set by Kong for public route)
4. `X-API-Key` header → validate against `API_KEYS` env var

### Good Behaviour mTLS Mode

Good Behaviour models a 3rd-party API that enforces mTLS. When `MTLS_ENABLED=true`, the container runs two gunicorn processes:
- Port 5443: HTTPS with mTLS (`--cert-reqs 2` = require client cert)
- Port 5000: Plain HTTP for Kubernetes liveness/readiness probes (HTTP probes can't do mTLS)

Kong acts as the mTLS client, presenting its client certificate when calling Good Behaviour.

### Model Citizen Settings

- `API_GATEWAY_URL` — URL for Dogcatcher calls (routed through Kong)
- `DOGCATCHER_PUBLIC_URL` — Used to rewrite internal photo URLs for browser access
- `GOOD_BEHAVIOUR_URL` — Points at Kong route (Kong adds mTLS to backend)
- `MOVIEZZZ_URL`, `FREE_PARKING_URL`, `PARK_RUNS_URL` — Called directly (no gateway)

## Key Files

- `.env.example` — All configurable environment variables with comments
- `docker-compose.yml` — Local development stack
- `docker-compose.azure.yml` — Azure-specific overrides
- `helm-chart/apigw-demo/values.yaml` — Kubernetes deployment values (CHANGE_ME placeholders)
- `helm-chart/apigw-demo/my-values.yaml` — Actual deployment values (gitignored)
- `docs/` — Kong config, mTLS setup, OIDC multi-auth guides
- `scripts/docker-build-push.sh` — Cross-platform (linux/amd64) image build/push
- `scripts/deploy-with-apisix.sh` — Alternative deployment with APISIX gateway
- `certs/mtls/` — mTLS certificates for local dev proxy
