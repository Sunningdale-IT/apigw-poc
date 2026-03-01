# Dogcatcher API Gateway POC

A proof-of-concept demonstrating API Gateway patterns with a Django-based dog catcher application. This project showcases multi-protocol authentication (Plain, API Key, JWT, mTLS, OIDC), API Gateway configuration with Kong, certificate management, and cloud-native Kubernetes deployment.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Model Citizen  │────▶│  Kong Gateway   │────▶│  Dogcatcher API │
│  (Django App)   │     │  (API Gateway)  │     │  (Django REST)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
        │                        │ mTLS (port 5443)
        │                        ▼
        │               ┌─────────────────┐
        │               │  Good Behaviour │  ◀── Good behaviour check
        │               │  (mTLS backend) │      Kong presents client cert
        │               └─────────────────┘      Good Behaviour verifies it
        │
        │               ┌──────────────────────────────────────────┐
        │               │   Certosaur (Certificate Management)     │
        │               │   Issues CA, server cert, client cert    │
        │               └──────────────────────────────────────────┘
        │
        │               ┌─────────────────┐     ┌─────────────────┐
        │               │    Keycloak     │     │   PostgreSQL    │
        │               │ (Identity Prov) │     │    Server       │
        │               └─────────────────┘     │  ┌───────────┐  │
        │                                       │  │  kong db  │  │
        │                                       │  │ dogcatcher│  │
        │                                       │  │ keycloak  │  │
        │                                       │  │ certosaur │  │
        │                                       │  │ moviezzz  │  │
        │                                       │  │ freepkg   │  │
        │                                       │  │ goodbehav │  │
        │                                       │  │ parkruns  │  │
        │  ┌────────────────────────────────┐   │  └───────────┘  │
        └─▶│  Demo Backend APIs             │   └─────────────────┘
           │  • Moviezzz (cinema listings)  │
           │  • Free Parking (spot finder)  │
           │  • Park Runs (running events)  │
           └────────────────────────────────┘
```

**Good Behaviour traffic flow:**

```
Citizen App ──(plain HTTP)──▶ Kong :8000/good-behaviour ──(mTLS :5443)──▶ Good Behaviour
  no client cert needed         Kong presents kong-client cert               verifies cert CN
                                Good Behaviour CA validates it               returns record
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
| Kong | 3.4 (with OIDC) | API Gateway (multi-protocol auth) |
| Apache APISIX | 3.x | Alternative API Gateway (comparison & migration) |
| etcd | 3.5.x | APISIX configuration storage |
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
| **Model Citizen App** | 5002 | citizen.* | Django citizen portal consuming all backend APIs |
| **Certosaur** | 8000 | certosaur.* | Certificate authority management portal |
| **Kong Gateway** | 8000 | kong.* | API Gateway with multi-protocol authentication |
| **Kong Admin API** | 8001 | kong-admin.* | Kong configuration API |
| **Kong Manager** | 8002 | kong-manager.* | Kong web admin interface |
| **Keycloak** | 8090 | keycloak.* | Identity Provider for OIDC authentication |
| **Moviezzz** | 5003 | moviezzz.* | Cinema and movie listings API |
| **Free Parking** | 5004 | free-parking.* | Available parking spots API |
| **Good Behaviour** | 5005 | good-behaviour.* | Good behaviour check API |
| **Park Runs** | 5006 | park-runs.* | Saturday park running events API |
| **PostgreSQL** | 5432 | Internal | Unified database server (8 databases) |

## Features

- **REST API** with Swagger/OpenAPI documentation (drf-spectacular)
- **Multi-protocol authentication**: Plain, API Key, JWT, mTLS, OIDC
- **Kong API Gateway** with OIDC plugin for OpenID Connect
- **Keycloak Identity Provider** for OIDC authentication
- **Certosaur Certificate Management** - Web-based CA for generating server and client certificates
- **Health Endpoints** - All applications expose `/health/` for Kubernetes probes
- **Kubernetes-native deployment** with Helm charts
- **Auto-generated TLS certificates** via cert-manager and Let's Encrypt
- **Unified PostgreSQL** - Single database server hosting multiple databases
- **Production-ready** - Optimized Docker images with multi-stage builds
- **Django Admin interface** for database management

## Demo Applications

This POC includes a suite of demo backend APIs that the **Model Citizen** portal consumes to demonstrate real service-to-service API calls through the gateway.

### Moviezzz - Cinema & Movie Listings

A Django REST API serving cinema and movie data. The Model Citizen portal displays current movies showing at local cinemas.

- **API**: `/api/movies/` - List all movies with showtimes and cinema details
- **API**: `/api/cinemas/` - List all cinemas
- **Health**: `/health/`
- **Test data**: Auto-populated on first deployment via `populate_movies` management command

### Free Parking - Available Parking Spots

A Django REST API providing real-time parking spot availability across the city.

- **API**: `/api/spots/` - List all parking spots (filter by `?available=true`)
- **Health**: `/health/`
- **Spot types**: Street, Garage, Lot, Disabled, EV Charging
- **Test data**: Auto-populated on first deployment via `populate_parking` management command

### Good Behaviour

A Django REST API for looking up citizen good behaviour records by citizen ID. This service is protected with **mutual TLS (mTLS)**: only Kong (presenting a trusted client certificate) can call it. The citizen app never calls it directly.

- **API**: `/api/citizens/` - List citizens
- **API**: `/api/citizens/check/{citizen_id}/` - Check a specific citizen's record
- **API**: `/api/records/` - List all good behaviour records
- **Health**: `/health/` (plain HTTP on port 5000, always reachable for k8s probes)
- **mTLS API**: port 5443 — HTTPS with mandatory client certificate (Kong only)
- **Test data**: Auto-populated on first deployment via `populate_records` management command

**mTLS behaviour:**

| Port | Protocol | Purpose | Who connects |
|------|----------|---------|--------------|
| 5000 | HTTP | Health checks only | Kubernetes probes |
| 5443 | HTTPS + client cert required | All API traffic | Kong (presents `kong-client` cert) |

### Park Runs - Saturday Running Events

A Django REST API listing Saturday park run events across the city.

- **API**: `/api/parkruns/` - List all park runs with distance, start time, and organiser details
- **Health**: `/health/`
- **Test data**: Auto-populated on first deployment via `populate_parkruns` management command

### Model Citizen Portal Integration

The **Model Citizen** app (`citizen-app/`) integrates all four new APIs alongside the existing Dogcatcher API. After logging in with a CitID (e.g. `DEMO`, `CIT001`, `CIT002`, `CIT003`), citizens can access:

| Service | URL Path | Backend API | Auth |
|---------|----------|-------------|------|
| Found Dogs | `/found-dogs/` | Dogcatcher via Kong | Kong injects API key |
| Movies | `/movies/` | Moviezzz (direct) | None |
| Parking | `/parking/` | Free Parking (direct) | None |
| Good Behaviour | `/good-behaviour/` | Good Behaviour **via Kong** (mTLS) | Kong presents client cert |
| Park Runs | `/park-runs/` | Park Runs (direct) | None |

The backend URLs are configured via environment variables:

```bash
MOVIEZZZ_URL=http://moviezzz:5000            # or https://moviezzz.{domain}
FREE_PARKING_URL=http://free-parking:5000    # or https://free-parking.{domain}
GOOD_BEHAVIOUR_URL=http://kong:8000/good-behaviour  # routes through Kong → mTLS to good-behaviour
PARK_RUNS_URL=http://park-runs:5000          # or https://park-runs.{domain}
```

> **Note:** `GOOD_BEHAVIOUR_URL` points at Kong, not at the good-behaviour service directly. Kong then establishes the mTLS connection to good-behaviour on port 5443. The citizen app sends a plain HTTP request with no client certificate.

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
docker build --platform linux/amd64 -t <your-registry>/certosaur:latest -f ../../certosaur/Dockerfile ../../certosaur
docker build --platform linux/amd64 -t <your-registry>/moviezzz:latest -f ../../moviezzz/Dockerfile ../../moviezzz
docker build --platform linux/amd64 -t <your-registry>/free-parking:latest -f ../../free-parking/Dockerfile ../../free-parking
docker build --platform linux/amd64 -t <your-registry>/good-behaviour:latest -f ../../good-behaviour/Dockerfile ../../good-behaviour
docker build --platform linux/amd64 -t <your-registry>/park-runs:latest -f ../../park-runs/Dockerfile ../../park-runs

# Push to registry
docker push <your-registry>/dogcatcher:latest
docker push <your-registry>/citizen:latest
docker push <your-registry>/certosaur:latest
docker push <your-registry>/moviezzz:latest
docker push <your-registry>/free-parking:latest
docker push <your-registry>/good-behaviour:latest
docker push <your-registry>/park-runs:latest

# 3. Configure your deployment
cp values.yaml my-values.yaml
# Edit my-values.yaml:
#   - Update global.domain to your domain
#   - Update image repositories if using custom registry
#   - Update ingress hosts

# 4. Create namespace
kubectl create namespace apigw-demo

# 5. Install with Helm - IMPORTANT: Set all passwords/secrets via command line
# DO NOT commit real passwords to values.yaml!
helm install apigw-demo . \
  --set postgres.env.password='<your-postgres-password>' \
  --set postgres.databases.kong.password='<kong-db-password>' \
  --set postgres.databases.dogcatcher.password='<dogcatcher-db-password>' \
  --set postgres.databases.keycloak.password='<keycloak-db-password>' \
  --set postgres.databases.certosaur.password='<certosaur-db-password>' \
  --set postgres.databases.moviezzz.password='<moviezzz-db-password>' \
  --set postgres.databases.freeparking.password='<freeparking-db-password>' \
  --set postgres.databases.goodbehaviour.password='<goodbehaviour-db-password>' \
  --set postgres.databases.parkruns.password='<parkruns-db-password>' \
  --set dogcatcher.env.secretKey='<dogcatcher-secret-key>' \
  --set dogcatcher.env.apiKeys='<dogcatcher-api-key>' \
  --set citizen.env.dogcatcherApiKey='<dogcatcher-api-key>' \
  --set citizen.env.secretKey='<citizen-secret-key>' \
  --set certosaur.env.secretKey='<certosaur-secret-key>' \
  --set moviezzz.env.secretKey='<moviezzz-secret-key>' \
  --set freeparking.env.secretKey='<freeparking-secret-key>' \
  --set goodbehaviour.env.secretKey='<goodbehaviour-secret-key>' \
  --set parkruns.env.secretKey='<parkruns-secret-key>' \
  --set keycloak.env.adminPassword='<keycloak-admin-password>' \
  -n apigw-demo

# Alternative: Use a separate secrets file (DO NOT commit to git!)
# Use the provided template:
cp secrets-template.yaml secrets.yaml

# Generate random passwords and fill in secrets.yaml:
DOGCATCHER_API_KEY="$(openssl rand -hex 32)"
cat > secrets.yaml <<EOF
postgres:
  env:
    password: "$(openssl rand -base64 32)"
  databases:
    kong:
      password: "$(openssl rand -base64 32)"
    dogcatcher:
      password: "$(openssl rand -base64 32)"
    keycloak:
      password: "$(openssl rand -base64 32)"
    certosaur:
      password: "$(openssl rand -base64 32)"
    moviezzz:
      password: "$(openssl rand -base64 32)"
    freeparking:
      password: "$(openssl rand -base64 32)"
    goodbehaviour:
      password: "$(openssl rand -base64 32)"
    parkruns:
      password: "$(openssl rand -base64 32)"
dogcatcher:
  env:
    secretKey: "$(openssl rand -base64 64)"
    apiKeys: "${DOGCATCHER_API_KEY}"
citizen:
  env:
    secretKey: "$(openssl rand -base64 64)"
    dogcatcherApiKey: "${DOGCATCHER_API_KEY}"
certosaur:
  env:
    secretKey: "$(openssl rand -base64 64)"
moviezzz:
  env:
    secretKey: "$(openssl rand -base64 64)"
freeparking:
  env:
    secretKey: "$(openssl rand -base64 64)"
goodbehaviour:
  env:
    secretKey: "$(openssl rand -base64 64)"
parkruns:
  env:
    secretKey: "$(openssl rand -base64 64)"
keycloak:
  env:
    adminPassword: "$(openssl rand -base64 32)"
EOF

# Verify secrets.yaml is in .gitignore (already configured)
# Install using values file + secrets file
helm install apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo

# 6. Monitor deployment
kubectl get pods -n apigw-demo -w

# 7. Check ingress and certificates
kubectl get ingress,certificates -n apigw-demo
```

#### Deploying with Apache APISIX (Side-by-Side with Kong)

The helm chart includes Apache APISIX as an optional subchart, allowing you to run both Kong and APISIX side-by-side for comparison and gradual migration.

**Update Helm dependencies** (required before first install):

```bash
cd helm-chart/apigw-demo
helm dependency update
```

This downloads the official Apache APISIX Helm chart into the `charts/` directory.

**Deploy with APISIX enabled**:

```bash
helm install apigw-demo . \
  --set apisix.enabled=true \
  --set apisix.admin.credentials.admin='your-secure-admin-key' \
  --set apisix.dashboard.config.conf.authentication.users[0].password='your-secure-password' \
  -n apigw-demo
```

**Access APISIX**:

- **Gateway**: https://apisix.your-domain.com
- **Dashboard**: https://apisix-dashboard.your-domain.com (admin/admin by default)
- **Admin API**: `http://apigw-demo-apisix-admin:9180/apisix/admin` (internal)

**Configuration**: See [APISIX-DEPLOYMENT.md](helm-chart/apigw-demo/APISIX-DEPLOYMENT.md) for detailed configuration options, plugin management, and route creation.

**Disable APISIX** (if needed):

```bash
helm upgrade apigw-demo . --set apisix.enabled=false -n apigw-demo
```

---

#### Connecting the Citizen App to Dogcatcher via Kong

The Citizen app calls Kong with no credentials. Kong holds the Dogcatcher API key internally and injects it into every upstream request before forwarding. The Citizen app never needs to know the key.

```
Citizen ──(no key)──▶ Kong (/dogcatcher/*) ──adds X-API-Key──▶ Dogcatcher
                        (request-transformer plugin)
```

---

##### Step 1 — Enable Kong ingresses

Add the following to `my-values.yaml` (skip if already done):

```yaml
kong:
  proxy:
    ingress:
      enabled: true
      host: kong.jim00.pd.test-rig.nl
  admin:
    ingress:
      enabled: true
      host: kong-admin.jim00.pd.test-rig.nl
  manager:
    ingress:
      enabled: true
      host: kong-manager.jim00.pd.test-rig.nl
```

Apply:

```bash
helm upgrade apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo
```

Wait for the Kong certificates to be issued before continuing:

```bash
kubectl get certificates -n apigw-demo -w
# Wait until kong-proxy-tls, kong-admin-tls, and kong-manager-tls all show Ready: True
```

---

##### Step 2 — Configure Kong via the Manager Portal

Open **https://kong-manager.jim00.pd.test-rig.nl** (no login required for OSS).

---

###### 2a — Create the service

This tells Kong where to find the Dogcatcher backend.

1. Left sidebar → **Gateway Services** → **New Gateway Service**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Name | `dogcatcher` |
   | URL | `http://apigw-demo-dogcatcher:5000/api` |

3. Click **Save**

---

###### 2b — Create the route

1. Click into **dogcatcher** → **Routes** → **New Route**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Name | `dogcatcher-route` |
   | Paths | `/dogcatcher` |
   | Strip Path | ✅ enabled |

3. Click **Save**

> There is **no** key-auth plugin on this route — the inbound request from Citizen requires no credentials.

---

###### 2c — Add the request-transformer plugin

This is the only plugin needed. It adds the API key and auth bypass headers to every request Kong forwards to Dogcatcher.

1. Click into **dogcatcher-route** → **Plugins** → **New Plugin**
2. Select **Request Transformer**
3. Under **Add Headers** add three entries:

   | Header | Value |
   |--------|-------|
   | `X-API-Key` | `<your-dogcatcher-api-key>` |
   | `X-Auth-Mode` | `inject` |
   | `X-Auth-Verified` | `true` |

   Replace `<your-dogcatcher-api-key>` with the value set in `dogcatcher.env.apiKeys` in your helm values.

4. Click **Save**

---

###### 2d — Verify in the portal

- **Gateway Services** — `dogcatcher` is listed
- **Routes** — `dogcatcher-route` shows path `/dogcatcher` linked to the service
- **Plugins** on the route — `request-transformer` is listed as **Enabled**

---

##### Step 3 — Point the Citizen app at Kong

Update `my-values.yaml`:

```yaml
citizen:
  env:
    apiGatewayUrl: "http://apigw-demo-kong-proxy:8000/dogcatcher"
    dogcatcherApiKey: ""   # leave blank — Kong holds the key
```

Apply:

```bash
helm upgrade apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo
```

For Docker Compose, update `.env` and restart:

```bash
API_GATEWAY_URL=http://kong:8000/dogcatcher
DOGCATCHER_API_KEY=   # leave blank

docker compose up -d citizen
```

---

##### Step 4 — Verify

```bash
# No key needed from the caller — Kong adds it
curl -s -o /dev/null -w "%{http_code}" https://kong.jim00.pd.test-rig.nl/dogcatcher/dogs/
# Expected: 200

# Confirm the Citizen app is working end-to-end
curl -s https://citizen.jim00.pd.test-rig.nl/health/
```

You can also open **Kong Manager** at `https://kong-manager.jim00.pd.test-rig.nl` to inspect the configured service, route, and plugin visually.

---

##### Reverting to direct access

To switch the Citizen app back to calling Dogcatcher directly (bypassing Kong), restore these values in `my-values.yaml`:

```yaml
citizen:
  env:
    apiGatewayUrl: "http://apigw-demo-dogcatcher:5000/api"
    dogcatcherApiKey: "<your-dogcatcher-api-key>"
```

---

#### Connecting Good Behaviour via Kong with mTLS

The Good Behaviour service is protected with mutual TLS. The citizen app calls Kong over plain HTTP; Kong then presents a client certificate when forwarding the request to good-behaviour on port 5443.

```
Citizen App ──(plain HTTP)──▶ Kong :8000/good-behaviour ──(mTLS :5443)──▶ Good Behaviour
  no client cert                Kong presents kong-client cert                verifies cert CN
```

##### Overview of what is needed

| Component | What is needed |
|-----------|----------------|
| Good Behaviour | Server TLS cert + key; CA cert to verify Kong's client cert |
| Kong | Client cert + key to present to good-behaviour; CA cert to verify good-behaviour's server cert |
| Helm secret | All five PEM values stored in `apigw-demo-good-behaviour-mtls` |

---

##### Step 1 — Generate the certificates using Certosaur

Certosaur is the internal certificate authority for this project. Use it to issue all the required certificates.

1. Open Certosaur at **https://certosaur.{your-domain}/**
2. Log in and navigate to **Certificate Authorities**
3. Note the **government** intermediate CA (created automatically on first deploy) — use this as the signing CA for good-behaviour

**Create the Good Behaviour server certificate:**

1. Navigate to **Server Certificates** → **New Server Certificate**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Common Name | `good-behaviour` |
   | Organisation | `Sunningdale IT` |
   | Signed by | `government` (intermediate CA) |
   | SANs (DNS) | `good-behaviour`, `apigw-demo-goodbehaviour`, `apigw-demo-goodbehaviour.apigw-demo.svc.cluster.local` |

3. Click **Create** then download:
   - **Certificate** → save as `good-behaviour-server.crt`
   - **Key** → save as `good-behaviour-server.key`
   - **Chain** → this is the full chain including the intermediate CA

**Create the Kong client certificate:**

1. Navigate to **Client Certificates** → **New Client Certificate**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Common Name | `kong-client` |
   | Organisation | `Sunningdale IT` |
   | Signed by | `government` (intermediate CA) |

3. Click **Create** then download:
   - **Certificate** → save as `kong-client.crt`
   - **Key** → save as `kong-client.key`

**Download the CA certificate:**

1. Navigate to **Certificate Authorities** → click **government**
2. Download **Certificate** → save as `good-behaviour-ca.crt`

   > Use the intermediate CA cert here, not the root. Good-behaviour will trust any client cert signed by this CA.

---

##### Step 2 — Enable mTLS in Helm values

Add the following to your `secrets.yaml` (never commit real cert material to `my-values.yaml`):

```yaml
goodbehaviour:
  mtls:
    enabled: true
    requiredClientCN: "kong-client"
    caCert: |
      -----BEGIN CERTIFICATE-----
      <paste good-behaviour-ca.crt content here>
      -----END CERTIFICATE-----
    serverCert: |
      -----BEGIN CERTIFICATE-----
      <paste good-behaviour-server.crt content here>
      -----END CERTIFICATE-----
    serverKey: |
      -----BEGIN PRIVATE KEY-----
      <paste good-behaviour-server.key content here>
      -----END PRIVATE KEY-----
    clientCert: |
      -----BEGIN CERTIFICATE-----
      <paste kong-client.crt content here>
      -----END CERTIFICATE-----
    clientKey: |
      -----BEGIN PRIVATE KEY-----
      <paste kong-client.key content here>
      -----END PRIVATE KEY-----
```

Alternatively, pass them as `--set` flags using file substitution:

```bash
helm upgrade apigw-demo . \
  -f my-values.yaml \
  -f secrets.yaml \
  --set goodbehaviour.mtls.enabled=true \
  --set goodbehaviour.mtls.requiredClientCN=kong-client \
  --set-file goodbehaviour.mtls.caCert=good-behaviour-ca.crt \
  --set-file goodbehaviour.mtls.serverCert=good-behaviour-server.crt \
  --set-file goodbehaviour.mtls.serverKey=good-behaviour-server.key \
  --set-file goodbehaviour.mtls.clientCert=kong-client.crt \
  --set-file goodbehaviour.mtls.clientKey=kong-client.key \
  -n apigw-demo
```

Also update `my-values.yaml` to point the citizen app at Kong for good behaviour checks:

```yaml
citizen:
  env:
    goodBehaviourUrl: "http://apigw-demo-kong-proxy:8000/good-behaviour"
```

Apply the upgrade:

```bash
helm upgrade apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo
```

Wait for the good-behaviour pod to restart and confirm it is listening on both ports:

```bash
kubectl get pods -n apigw-demo -l app.kubernetes.io/component=goodbehaviour
kubectl logs deployment/apigw-demo-goodbehaviour -n apigw-demo | grep "Starting good-behaviour"
# Expected: Starting good-behaviour with mTLS on port 5443 (plain HTTP health on 5000)
```

---

##### Step 3 — Configure Kong via the Manager Portal

Open **https://kong-manager.{your-domain}** (no login required for OSS).

---

###### 3a — Create the service (HTTPS upstream with client cert)

First, register the Kong client certificate in Kong so it can present it to good-behaviour:

1. Left sidebar → **Certificates** → **New Certificate**
2. Paste the contents of `kong-client.crt` into **Certificate** and `kong-client.key` into **Key**
3. Click **Save** and note the certificate ID (shown in the URL or list)

Next, register the good-behaviour CA so Kong can verify the server certificate:

1. Left sidebar → **CA Certificates** → **New CA Certificate**
2. Paste the contents of `good-behaviour-ca.crt` into **Certificate**
3. Click **Save** and note the CA certificate ID

Now create the service:

1. Left sidebar → **Gateway Services** → **New Gateway Service**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Name | `good-behaviour` |
   | Protocol | `https` |
   | Host | `apigw-demo-goodbehaviour` |
   | Port | `5443` |
   | Path | `/api/citizens` |
   | TLS Verify | ✅ enabled |
   | CA Certificates | select the CA cert registered above |
   | Client Certificate | select the client cert registered above |

3. Click **Save**

---

###### 3b — Create the route (plain HTTP inbound from citizen app)

1. Click into **good-behaviour** → **Routes** → **New Route**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | Name | `good-behaviour` |
   | Paths | `/good-behaviour` |
   | Methods | `GET`, `POST` |
   | Strip Path | ✅ enabled |

3. Click **Save**

> There is **no** authentication plugin on this route — the citizen app calls it with plain HTTP and no credentials. Security is enforced at the Kong → good-behaviour leg via mTLS.

---

###### 3c — Verify in the portal

- **Gateway Services** — `good-behaviour` is listed with protocol `https` and port `5443`
- **Routes** — `good-behaviour` shows path `/good-behaviour` linked to the service
- **Certificates** — `kong-client` cert is listed
- **CA Certificates** — `good-behaviour-ca` cert is listed

---

##### Step 4 — Verify end-to-end

```bash
# Confirm good-behaviour health check works on plain HTTP (no cert)
kubectl exec -n apigw-demo deployment/apigw-demo-goodbehaviour -- \
  wget -qO- http://localhost:5000/health/
# Expected: {"status": "healthy", ...}

# Confirm Kong can reach good-behaviour via mTLS (from inside the cluster)
kubectl exec -n apigw-demo deployment/apigw-demo-kong -- \
  wget -qO- http://localhost:8000/good-behaviour/check/CIT001/
# Expected: citizen record JSON

# Confirm the citizen app good behaviour page works end-to-end
curl -s https://citizen.{your-domain}/good-behaviour/?citizen_id=CIT001
# Expected: HTML page with citizen record
```

**Test that direct access to good-behaviour is blocked (no client cert):**

```bash
# This should fail with a TLS handshake error — no client cert presented
kubectl run test-curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sk https://apigw-demo-goodbehaviour.apigw-demo.svc.cluster.local:5443/health/
# Expected: SSL handshake failure or connection reset
```

---

##### Troubleshooting mTLS

**Good-behaviour pod fails to start:**

```bash
kubectl logs deployment/apigw-demo-goodbehaviour -n apigw-demo
# Look for: "ERROR: mTLS enabled but server cert not found at /app/certs/server.crt"
# Fix: Verify the secret was created correctly
kubectl get secret apigw-demo-good-behaviour-mtls -n apigw-demo -o yaml
```

**Kong cannot connect to good-behaviour (SSL error):**

```bash
kubectl logs deployment/apigw-demo-kong -n apigw-demo | grep -i "good-behaviour\|ssl\|tls"
# Common causes:
# - CA cert not registered in Kong (Kong cannot verify good-behaviour's server cert)
# - Client cert not attached to the Kong service
# - SAN mismatch: good-behaviour server cert must include the k8s service hostname
```

**403 Forbidden from good-behaviour (CN mismatch):**

```bash
# The client cert CN does not match MTLS_REQUIRED_CN
# Check what CN Kong is presenting:
kubectl logs deployment/apigw-demo-goodbehaviour -n apigw-demo | grep "CN mismatch"
# Fix: Ensure the Kong client cert has CN=kong-client and goodbehaviour.mtls.requiredClientCN=kong-client
```

**Citizen app shows "Unable to connect to records database":**

```bash
# Check GOOD_BEHAVIOUR_URL is set to the Kong route, not the direct service
kubectl exec -n apigw-demo deployment/apigw-demo-citizen -- env | grep GOOD_BEHAVIOUR
# Expected: GOOD_BEHAVIOUR_URL=http://apigw-demo-kong-proxy:8000/good-behaviour
```

---

##### Disabling mTLS (reverting to direct access)

To switch good-behaviour back to plain HTTP (bypassing mTLS), update `my-values.yaml`:

```yaml
goodbehaviour:
  mtls:
    enabled: false

citizen:
  env:
    goodBehaviourUrl: "http://apigw-demo-goodbehaviour:5000"
```

Apply:

```bash
helm upgrade apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo
```

---

#### Helm Chart Configuration

The Helm chart (`helm-chart/apigw-demo/`) includes:

- **Unified PostgreSQL StatefulSet** - Single database server with 8 databases (kong, dogcatcher, keycloak, certosaur, moviezzz, freeparking, goodbehaviour, parkruns)
- **11 Application Deployments** - Dogcatcher, Kong, Citizen, Certosaur, Keycloak, Moviezzz, Free Parking, Good Behaviour, Park Runs
- **Health Checks** - All apps have liveness and readiness probes using `/health/` endpoints
- **TLS Ingresses** - Automatic certificate generation via cert-manager
- **PersistentVolumes** - For database data, uploads, and certificates
- **ConfigMaps & Secrets** - Externalized configuration
- **Automatic Test Data** - All backend APIs auto-populate with test data on first deployment

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
    certosaur:
      name: certosaur
      username: certosaur
    moviezzz:
      name: moviezzz
      username: moviezzz
    freeparking:
      name: freeparking
      username: freeparking
    goodbehaviour:
      name: goodbehaviour
      username: goodbehaviour
    parkruns:
      name: parkruns
      username: parkruns

dogcatcher:
  replicaCount: 2
  image:
    repository: docker.io/jimleitch/dogcatcher
  env:
    apiKeyRequired: "true"      # Require API key on all requests
    apiKeys: "<your-api-key>"   # Set via --set or secrets.yaml
  testData:
    count: "50"                 # Number of test dogs on first deploy
  ingress:
    host: dogcatcher.jim00.pd.test-rig.nl

kong:
  replicaCount: 2
  ingress:
    host: kong.jim00.pd.test-rig.nl

citizen:
  replicaCount: 2
  env:
    dogcatcherApiKey: "<your-api-key>"  # Must match dogcatcher.env.apiKeys
  ingress:
    host: citizen.jim00.pd.test-rig.nl

moviezzz:
  enabled: true
  ingress:
    hosts:
      - host: moviezzz.jim00.pd.test-rig.nl

freeparking:
  enabled: true
  ingress:
    hosts:
      - host: free-parking.jim00.pd.test-rig.nl

goodbehaviour:
  enabled: true
  ingress:
    hosts:
      - host: good-behaviour.jim00.pd.test-rig.nl
  # mTLS — set in secrets.yaml, not here
  mtls:
    enabled: true                    # set false to disable mTLS
    requiredClientCN: "kong-client"  # CN that Kong's client cert must present
    caCert: ""                       # set via secrets.yaml or --set-file
    serverCert: ""
    serverKey: ""
    clientCert: ""
    clientKey: ""

parkruns:
  enabled: true
  ingress:
    hosts:
      - host: park-runs.jim00.pd.test-rig.nl
```

#### Accessing Applications (Kubernetes)

After deployment, applications are available at:

- **Dogcatcher API**: https://dogcatcher.{your-domain}/api/docs/
- **Dogcatcher Admin**: https://dogcatcher.{your-domain}/admin/
- **Model Citizen**: https://citizen.{your-domain}/
- **Certosaur**: https://certosaur.{your-domain}/login/
- **Kong Proxy**: https://kong.{your-domain}/
- **Kong Admin**: https://kong-admin.{your-domain}/
- **Kong Manager**: https://kong-manager.{your-domain}/
- **Keycloak**: https://keycloak.{your-domain}/
- **Moviezzz**: https://moviezzz.{your-domain}/api/movies/
- **Free Parking**: https://free-parking.{your-domain}/api/spots/
- **Good Behaviour**: https://good-behaviour.{your-domain}/api/citizens/
- **Park Runs**: https://park-runs.{your-domain}/api/parkruns/

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

# Uninstall (PostgreSQL data will be preserved)
helm uninstall apigw-demo -n apigw-demo

# Note: PostgreSQL PersistentVolumeClaim is retained after uninstall
# This allows data to persist across reinstalls
# To completely remove including data:
kubectl delete pvc postgres-data-apigw-demo-postgres-0 -n apigw-demo
```

#### Data Persistence

**PostgreSQL Database Persistence:**

The PostgreSQL StatefulSet uses a PersistentVolumeClaim (PVC) with the `helm.sh/resource-policy: keep` annotation, which means:

✅ **Database data persists across Helm uninstall/reinstall**
- When you run `helm uninstall`, the PVC is NOT deleted
- When you reinstall with `helm install`, it reuses the existing PVC
- All databases (kong, dogcatcher, keycloak, certosaur) and their data are preserved

**Managing Persistent Data:**

```bash
# List PVCs to see database storage
kubectl get pvc -n apigw-demo

# Check PVC details and status
kubectl describe pvc postgres-data-apigw-demo-postgres-0 -n apigw-demo

# Uninstall Helm release (data is kept)
helm uninstall apigw-demo -n apigw-demo

# Reinstall (will reuse existing database)
helm install apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo

# To completely wipe data and start fresh:
# 1. Uninstall release
helm uninstall apigw-demo -n apigw-demo

# 2. Delete the PVC
kubectl delete pvc postgres-data-apigw-demo-postgres-0 -n apigw-demo

# 3. Reinstall (will create new empty database)
helm install apigw-demo . -f my-values.yaml -f secrets.yaml -n apigw-demo
```

**⚠️ Important Notes:**
- Database passwords in the PVC must match the passwords used during reinstall
- If you change database passwords, you'll need to either:
  - Delete the PVC and start fresh, OR
  - Manually update passwords in the existing database
- Backup your database regularly using `pg_dump`:
  ```bash
  kubectl exec -n apigw-demo apigw-demo-postgres-0 -- \
    pg_dumpall -U postgres > backup.sql
  ```

#### Test Data Population

**Automatic Dogcatcher Test Data:**

The Dogcatcher application automatically populates with test data on first deployment using a Django management command that runs as an init container.

**Features:**
- ✅ **50 cute test dogs** created automatically when database is empty
- ✅ **Smart detection** - only populates if no dogs exist yet
- ✅ **Randomized data** - names, breeds, colors, locations, and comments
- ✅ **Configurable** - change the number of dogs via Helm values

**Configuration:**

```yaml
# In values.yaml or via --set flag
dogcatcher:
  testData:
    count: "50"  # Number of test dogs to create
```

**Override the count during deployment:**

```bash
# Create 100 test dogs instead of 50
helm install apigw-demo . \
  --set dogcatcher.testData.count=100 \
  -f secrets.yaml -n apigw-demo
```

**How it works:**

1. Init container runs after database migrations
2. Executes: `python manage.py populate_test_data --count 50`
3. Command checks if dogs already exist
4. If database is empty, creates test dogs with:
   - Random dog names (Buddy, Max, Charlie, etc.)
   - Random breeds (Labrador, Golden Retriever, etc.)
   - Random colors, locations, and descriptive comments
5. If dogs exist, does nothing (safe for redeployments)

**Manually populate test data:**

```bash
# SSH into dogcatcher pod
kubectl exec -it deployment/apigw-demo-dogcatcher -n apigw-demo -- bash

# Run the management command
python manage.py populate_test_data --count 100

# Or force repopulation (warning: deletes existing data!)
python manage.py populate_test_data --count 50 --force
```

**Verify test data:**

```bash
# Check number of dogs in database
kubectl exec -it deployment/apigw-demo-dogcatcher -n apigw-demo -- \
  python manage.py shell -c "from dogs.models import Dog; print(f'Dogs: {Dog.objects.count()}')"

# Or via the API
curl https://dogcatcher.{your-domain}/api/dogs/
```

#### Security Best Practices

**⚠️ IMPORTANT: The default `values.yaml` contains dummy passwords (`CHANGE_ME`) and must not be used in production!**

**Secrets Management:**

1. **Never commit real passwords to Git**
   - All passwords in `values.yaml` are set to `CHANGE_ME`
   - Always override via `--set` flags or separate secrets file
   - Add any secrets files to `.gitignore`

2. **Generate strong random secrets:**
   ```bash
   # Generate a random password
   openssl rand -base64 32
   
   # Generate a Django secret key
   openssl rand -base64 64
   ```

3. **Use Kubernetes Secrets (Recommended for Production):**
   ```bash
   # Create a secret for database passwords
   kubectl create secret generic postgres-passwords \
     --from-literal=postgres-password=$(openssl rand -base64 32) \
     --from-literal=kong-password=$(openssl rand -base64 32) \
     --from-literal=dogcatcher-password=$(openssl rand -base64 32) \
     --from-literal=keycloak-password=$(openssl rand -base64 32) \
     --from-literal=certosaur-password=$(openssl rand -base64 32) \
     -n apigw-demo
   
   # Create a secret for Django secret keys
   kubectl create secret generic django-secrets \
     --from-literal=dogcatcher-secret=$(openssl rand -base64 64) \
     --from-literal=citizen-secret=$(openssl rand -base64 64) \
     --from-literal=certosaur-secret=$(openssl rand -base64 64) \
     -n apigw-demo
   ```
   
   Then modify the deployment templates to reference these secrets instead of values.

4. **Use external secret management:**
   - Consider using [External Secrets Operator](https://external-secrets.io/)
   - Integrate with Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault
   - Automatically sync secrets from external providers

5. **Rotate credentials regularly:**
   ```bash
   # Update secrets with new values
   helm upgrade apigw-demo . \
     --set postgres.env.password='<new-password>' \
     --reuse-values \
     -n apigw-demo
   
   # Restart affected pods to pick up new secrets
   kubectl rollout restart deployment/apigw-demo-dogcatcher -n apigw-demo
   ```

**Security Checklist:**
- ✅ Generate unique passwords for each database
- ✅ Use strong Django secret keys (64+ random characters)
- ✅ Change default Keycloak admin password
- ✅ Enable HTTPS for all ingresses (cert-manager configured by default)
- ✅ Review and restrict ALLOWED_HOSTS in Django settings
- ✅ Configure network policies to restrict pod-to-pod communication
- ✅ Enable audit logging for sensitive operations
- ✅ Regularly update Docker images for security patches
- ✅ Enable mTLS for good-behaviour (`goodbehaviour.mtls.enabled: true`) — prevents direct access bypassing Kong
- ✅ Store mTLS certificate material in `secrets.yaml` (never commit to git)

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

Demo Backend APIs:
  Moviezzz:    http://localhost:5003/api/movies/
  Free Parking:http://localhost:5004/api/spots/
  Good Behav.: http://localhost:5005/api/citizens/
  Park Runs:   http://localhost:5006/api/parkruns/

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
├── certosaur/                        # Certificate Management Portal
│   ├── manage.py                     # Django management script
│   ├── certosaur_project/            # Django project configuration
│   ├── certificates/                 # Certificates Django app
│   │   ├── views.py                  # Includes /health/ endpoint
│   │   ├── cert_utils.py             # Certificate generation utilities
│   │   └── models.py                 # CA, Server, Client cert models
│   ├── templates/                    # HTML templates
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── moviezzz/                         # Moviezzz - Cinema & Movie Listings API
│   ├── manage.py                     # Django management script
│   ├── moviezzz_project/             # Django project configuration
│   ├── movies/                       # Movies Django app
│   │   ├── models.py                 # Cinema and Movie models
│   │   ├── views.py                  # REST API + /health/ endpoint
│   │   └── management/commands/      # populate_movies management command
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── free-parking/                     # Free Parking - Available Spots API
│   ├── manage.py                     # Django management script
│   ├── freeparking_project/          # Django project configuration
│   ├── parking/                      # Parking Django app
│   │   ├── models.py                 # ParkingSpot model
│   │   ├── views.py                  # REST API + /health/ endpoint
│   │   └── management/commands/      # populate_parking management command
│   ├── Dockerfile                    # Multi-stage optimized build
│   └── requirements.txt
├── good-behaviour/                   # Good Behaviour API (mTLS protected)
│   ├── manage.py                     # Django management script
│   ├── entrypoint.sh                 # Starts gunicorn in plain HTTP or mTLS mode
│   ├── goodbehaviour_project/        # Django project configuration
│   │   └── settings.py               # MTLS_ENABLED / MTLS_REQUIRED_CN env vars
│   ├── records/                      # Records Django app
│   │   ├── models.py                 # Citizen and CriminalRecord models (internal domain)
│   │   ├── middleware.py             # mTLS CN enforcement middleware
│   │   ├── views.py                  # REST API + /health/ endpoint
│   │   └── management/commands/      # populate_records management command
│   ├── Dockerfile                    # Multi-stage build; exposes 5000 (HTTP) + 5443 (mTLS)
│   └── requirements.txt
├── park-runs/                        # Park Runs - Saturday Running Events API
│   ├── manage.py                     # Django management script
│   ├── parkruns_project/             # Django project configuration
│   ├── runs/                         # Runs Django app
│   │   ├── models.py                 # ParkRun model
│   │   ├── views.py                  # REST API + /health/ endpoint
│   │   └── management/commands/      # populate_parkruns management command
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
│       │   ├── certosaur-deployment.yaml      # Cert management
│       │   ├── keycloak-deployment.yaml       # Identity provider
│       │   ├── moviezzz-deployment.yaml       # Cinema listings API
│       │   ├── freeparking-deployment.yaml    # Parking spots API
│       │   ├── goodbehaviour-deployment.yaml  # Good Behaviour API
│       │   ├── parkruns-deployment.yaml       # Park runs API
│       │   ├── kong-migrations-job.yaml       # DB init job
│       │   ├── secrets.yaml                   # All secrets (incl. good-behaviour mTLS certs)
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
API_GATEWAY_URL=http://web:5000/api
DOGCATCHER_API_KEY=<must-match-DOGCATCHER_API_KEYS>
DOGCATCHER_PUBLIC_URL=http://localhost:5001
```

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 5001 | Dogcatcher | Direct API access |
| 5002 | Model Citizen | Citizen portal |
| 5003 | Moviezzz | Cinema and movie listings API |
| 5004 | Free Parking | Available parking spots API |
| 5005 | Good Behaviour | Good behaviour check API |
| 5006 | Park Runs | Saturday park running events API |
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

The Helm chart uses a **single PostgreSQL StatefulSet** hosting eight separate databases:

| Database | User | Used By | Purpose |
|----------|------|---------|---------|
| `kong` | kong | Kong Gateway | Gateway configuration and state |
| `dogcatcher` | dogcatcher | Dogcatcher API | Dog registry data |
| `keycloak` | keycloak | Keycloak | Identity and access management |
| `certosaur` | certosaur | Certosaur | Certificate authority data |
| `moviezzz` | moviezzz | Moviezzz API | Cinema and movie listings |
| `freeparking` | freeparking | Free Parking API | Parking spot availability |
| `goodbehaviour` | goodbehaviour | Good Behaviour API | Behaviour records |
| `parkruns` | parkruns | Park Runs API | Saturday running events |

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
   - Django SECRET_KEY (Dogcatcher, Citizen, Certosaur, Moviezzz, Free Parking, Good Behaviour, Park Runs)
   - PostgreSQL passwords (postgres master, kong, dogcatcher, keycloak, certosaur, moviezzz, freeparking, goodbehaviour, parkruns)
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
| Certosaur DB User | `certosaur` / `certosaur123` | values.yaml → postgres.databases.certosaur.password |
| Moviezzz DB User | `moviezzz` / `moviezzz123` | values.yaml → postgres.databases.moviezzz.password |
| Free Parking DB User | `freeparking` / `freeparking123` | values.yaml → postgres.databases.freeparking.password |
| Good Behaviour DB User | `goodbehaviour` / `goodbehaviour123` | values.yaml → postgres.databases.goodbehaviour.password |
| Park Runs DB User | `parkruns` / `parkruns123` | values.yaml → postgres.databases.parkruns.password |
| Keycloak Admin | `admin` / `admin` | values.yaml → keycloak.env.adminPassword |
| Dogcatcher API Key | `CHANGE_ME` | values.yaml → dogcatcher.env.apiKeys (also set citizen.env.dogcatcherApiKey to match) |
| Django Admin | Create via manage.py | Run createsuperuser in pod |

**Docker Compose:**
| Item | Value |
|------|-------|
| Django Admin | `admin` / `admin123` |
| Keycloak Admin | `admin` / `admin` |
| Dogcatcher API Key | set `DOGCATCHER_API_KEYS` and `DOGCATCHER_API_KEY` to the same value in `.env` |
| Kong API Key (demo) | `citizen-api-key-2026` (Kong routes only, not used by Citizen app) |
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

**Good Behaviour mTLS issues:**
- See the dedicated troubleshooting section under [Connecting Good Behaviour via Kong with mTLS](#connecting-good-behaviour-via-kong-with-mtls)
- Quick check: `kubectl logs deployment/apigw-demo-goodbehaviour -n apigw-demo | grep -E "mTLS|ERROR|Starting"`
- Verify the mTLS secret exists: `kubectl get secret apigw-demo-good-behaviour-mtls -n apigw-demo`

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
