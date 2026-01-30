# Dogcatcher API Gateway Proxy - Multi-Protocol Authentication

This document describes the nginx-based proxy that sits in front of the Dogcatcher API, providing multiple authentication methods through different URL paths.

## Architecture

```
                              ┌─────────────────────────────────────┐
                              │         Nginx Proxy                 │
                              │      (dogcatcher-proxy)             │
                              │                                     │
   ┌──────────────────────────┼─────────────────────────────────────┼──────────────────────────┐
   │                          │                                     │                          │
   │  Port 80/443             │  Port 8443                          │                          │
   │  (HTTP/HTTPS)            │  (mTLS only)                        │                          │
   │                          │                                     │                          │
   │  ┌─────────────────────────────────────────────────────────┐   │                          │
   │  │                    Path Routing                          │   │                          │
   │  └─────────────────────────────────────────────────────────┘   │                          │
   │       │          │          │          │          │             │                          │
   │       ▼          ▼          ▼          ▼          ▼             │                          │
   │   /plain/    /apikey/    /mtls/     /jwt/     /oidc/           │                          │
   │       │          │          │          │          │             │                          │
   │   No Auth    API Key    Client    JWT Token   OIDC             │                          │
   │              Header      Cert     Validate    Flow             │                          │
   │       │          │          │          │          │             │                          │
   └───────┼──────────┼──────────┼──────────┼──────────┼─────────────┘                          │
           │          │          │          │          │                                        │
           └──────────┴──────────┴──────────┴──────────┘                                        │
                                    │                                                           │
                                    ▼                                                           │
                         ┌──────────────────┐                                                   │
                         │  Dogcatcher API  │                                                   │
                         │  (dogcatcher-web)│                                                   │
                         │    Port 5000     │                                                   │
                         └──────────────────┘                                                   │
```

## Authentication Modes

### 1. Plain - No Authentication (`/plain/`)

Open access without any authentication. Useful for public endpoints or development.

```bash
# Example
curl http://localhost:8080/plain/dogs/

# Response: Direct API response
```

### 2. API Key (`/apikey/`)

Requires `X-API-Key` header. The proxy validates presence; the backend validates the key value.

```bash
# Example
curl http://localhost:8080/apikey/dogs/ \
  -H "X-API-Key: your-api-key-here"

# Without API key: 401 Unauthorized
curl http://localhost:8080/apikey/dogs/
# {"error": "API key required", "message": "Provide X-API-Key header"}
```

### 3. mTLS - Mutual TLS (`/mtls/`)

Requires valid client certificate signed by the trusted CA.

```bash
# With client certificate
curl https://localhost:8443/mtls/dogs/ \
  --cacert certs/mtls/ca.crt \
  --cert certs/mtls/kong-client.crt \
  --key certs/mtls/kong-client.key

# Without certificate: 403 Forbidden
curl https://localhost:8443/mtls/dogs/ \
  --cacert certs/mtls/ca.crt
# {"error": "mTLS required", "message": "Valid client certificate required"}
```

### 4. JWT - Bearer Token (`/jwt/`)

Requires `Authorization: Bearer <token>` header.

```bash
# With JWT token
curl http://localhost:8080/jwt/dogs/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Without token: 401 Unauthorized
curl http://localhost:8080/jwt/dogs/
# {"error": "JWT required", "message": "Provide Authorization: Bearer <token>"}
```

**Note:** Full JWT validation requires additional setup (see JWT Validation section below).

### 5. OIDC - OpenID Connect (`/oidc/`)

Requires OIDC authentication flow with OAuth2 Proxy.

```bash
# Requires browser-based OIDC flow
# Or pass OIDC headers for testing:
curl http://localhost:8080/oidc/dogs/ \
  -H "X-OIDC-User: user@example.com" \
  -H "X-OIDC-Email: user@example.com"
```

**Note:** Full OIDC requires OAuth2 Proxy setup (see OIDC Setup section below).

### 6. Direct API Access (`/api/`)

Direct access to the Dogcatcher API, using its native authentication.

```bash
curl http://localhost:8080/api/dogs/ \
  -H "X-API-Key: your-api-key"
```

## Quick Start

### 1. Start the Services

```bash
# Create .env file with API keys
cat > .env << 'EOF'
DOGCATCHER_API_KEYS=test-key-123,another-key-456
API_KEY_REQUIRED=true
FLASK_DEBUG=true
EOF

# Start all services
docker compose up -d

# Check services
docker compose ps
```

### 2. Test Each Authentication Mode

```bash
# Plain (no auth)
curl http://localhost:8080/plain/dogs/

# API Key
curl http://localhost:8080/apikey/dogs/ \
  -H "X-API-Key: test-key-123"

# JWT (dev mode accepts any token)
curl http://localhost:8080/jwt/dogs/ \
  -H "Authorization: Bearer any-token-for-dev"

# OIDC (dev mode uses headers)
curl http://localhost:8080/oidc/dogs/ \
  -H "X-OIDC-User: testuser"

# mTLS (requires certs)
./scripts/generate-mtls-certs.sh
curl https://localhost:8443/mtls/dogs/ \
  --cacert certs/mtls/ca.crt \
  --cert certs/mtls/kong-client.crt \
  --key certs/mtls/kong-client.key \
  -k
```

### 3. View Swagger Documentation

Open http://localhost:8080/api/docs in your browser.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXY_MODE` | `dev` | `dev` or `prod` |
| `ENABLE_HTTPS` | `false` | Enable HTTPS (requires certs) |
| `ENABLE_MTLS` | `false` | Enable mTLS verification |
| `DOMAIN` | `localhost` | Domain for Let's Encrypt |
| `CA_CERT_PATH` | - | Path to CA cert for mTLS |

### Ports

| Port | Protocol | Description |
|------|----------|-------------|
| 8080 | HTTP | Multi-protocol routing |
| 8443 | HTTPS | TLS-encrypted access |
| 8444 | mTLS | Strict client cert required |
| 5001 | HTTP | Direct Dogcatcher access (bypass proxy) |

## JWT Validation Setup

For production JWT validation, you have several options:

### Option A: External JWT Validator Service

Create a simple JWT validation service:

```yaml
# Add to docker-compose.yml
jwt-validator:
  image: your-jwt-validator:latest
  environment:
    JWT_SECRET: your-jwt-secret
    JWT_ISSUER: your-issuer
```

### Option B: nginx with njs Module

Create `/proxy/njs/jwt.js`:

```javascript
function validate(r) {
    var auth = r.headersIn['Authorization'];
    if (!auth || !auth.startsWith('Bearer ')) {
        r.return(401, '{"error": "Invalid token"}');
        return;
    }
    
    var token = auth.substring(7);
    // Validate JWT here...
    
    r.return(200);
}

export default { validate };
```

### Option C: Use Kong Gateway

For production, consider using Kong which has built-in JWT plugin support.

## OIDC Setup

For production OIDC, deploy OAuth2 Proxy:

```yaml
# Add to docker-compose.yml
oauth2-proxy:
  image: quay.io/oauth2-proxy/oauth2-proxy:latest
  environment:
    OAUTH2_PROXY_PROVIDER: oidc
    OAUTH2_PROXY_OIDC_ISSUER_URL: https://your-idp.com
    OAUTH2_PROXY_CLIENT_ID: your-client-id
    OAUTH2_PROXY_CLIENT_SECRET: your-client-secret
    OAUTH2_PROXY_COOKIE_SECRET: random-32-byte-secret
    OAUTH2_PROXY_UPSTREAMS: http://dogcatcher-web:5000
  ports:
    - "4180:4180"
```

## Let's Encrypt Certificates

See [LETSENCRYPT-SETUP.md](./LETSENCRYPT-SETUP.md) for detailed instructions.

Quick setup:

```bash
./scripts/setup-letsencrypt.sh \
  --domain dogcatcher.example.com \
  --email admin@example.com
```

## Headers Passed to Backend

The proxy adds authentication context headers:

| Header | Description |
|--------|-------------|
| `X-Auth-Mode` | Authentication mode used (plain, apikey, mtls, jwt, oidc) |
| `X-Auth-Verified` | Whether auth was verified by proxy |
| `X-API-Key` | API key (for apikey mode) |
| `X-Client-Cert-DN` | Client certificate DN (for mtls mode) |
| `X-Client-Cert-Verified` | Certificate verification status |
| `X-JWT-Subject` | JWT subject claim (for jwt mode) |
| `X-OIDC-User` | OIDC username (for oidc mode) |
| `X-OIDC-Email` | OIDC email (for oidc mode) |

## Troubleshooting

### Check Proxy Logs

```bash
docker logs dogcatcher-proxy -f
```

### Test Proxy Health

```bash
curl http://localhost:8080/health
```

### Verify Certificate Configuration

```bash
# Check certificate
docker exec dogcatcher-proxy openssl x509 -in /etc/nginx/certs/server.crt -text -noout

# Test mTLS handshake
openssl s_client -connect localhost:8443 \
  -cert certs/mtls/kong-client.crt \
  -key certs/mtls/kong-client.key \
  -CAfile certs/mtls/ca.crt
```

### Common Issues

1. **502 Bad Gateway**: Backend not running
   - Check: `docker ps | grep dogcatcher-web`

2. **403 mTLS Required**: Client cert not provided or invalid
   - Verify cert: `openssl verify -CAfile ca.crt client.crt`

3. **401 API Key Required**: Missing X-API-Key header
   - Add header: `-H "X-API-Key: your-key"`

## Security Considerations

1. **Production Mode**: Set `PROXY_MODE=prod` for HTTPS redirect
2. **API Keys**: Use strong, random API keys
3. **mTLS Certificates**: Rotate certificates regularly
4. **Rate Limiting**: Configured at 10 req/s per IP
5. **HTTPS**: Use Let's Encrypt for production
