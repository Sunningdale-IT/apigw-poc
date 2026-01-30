# Kong mTLS Setup Guide

This guide covers configuring mutual TLS (mTLS) between Kong API Gateway and the Dogcatcher API, with Model Citizen connecting through Kong.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Model Citizen  │────▶│  Kong Gateway   │────▶│  Dogcatcher API  │
│                 │     │                 │     │                  │
│  HTTP Request   │     │  API Key Auth   │     │  mTLS Required   │
│                 │     │  + Client Cert  │     │  Verify Client   │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                              │
                              │ Uses:
                              │ - kong-client.crt
                              │ - kong-client.key
                              │ - ca.crt
                              │
                              ▼
                        Mutual TLS
                        (Two-way auth)
```

## What is mTLS?

Mutual TLS (mTLS) is a security mechanism where both the client and server authenticate each other using certificates:

1. **Server Authentication**: Client verifies server's certificate (like regular HTTPS)
2. **Client Authentication**: Server verifies client's certificate (additional security)

In our setup:
- **Dogcatcher API** presents its server certificate and requires clients to present a valid certificate
- **Kong** presents the client certificate when connecting to Dogcatcher
- **Model Citizen** connects to Kong via standard HTTP (Kong handles the mTLS complexity)

## Prerequisites

- Kubernetes cluster with Kong deployed
- `openssl` installed locally
- `kubectl` configured

## Step 1: Generate Certificates

Run the certificate generation script:

```bash
./scripts/generate-mtls-certs.sh

# Or with custom options:
./scripts/generate-mtls-certs.sh \
  --output-dir ./certs/mtls \
  --days 365 \
  --cn dogcatcher-api \
  --san "localhost,dogcatcher-api,dogcatcher-api.default.svc.cluster.local"
```

This creates:

| File | Description |
|------|-------------|
| `ca.crt` | CA certificate (trust anchor) |
| `ca.key` | CA private key (keep secure!) |
| `server.crt` | Dogcatcher server certificate |
| `server.key` | Dogcatcher server private key |
| `kong-client.crt` | Kong client certificate |
| `kong-client.key` | Kong client private key |
| `kong-client.pem` | Combined client cert + key |
| `k8s-mtls-secrets.yaml` | Kubernetes secrets manifest |

## Step 2: Deploy Certificates to Kubernetes

Apply the generated Kubernetes secrets:

```bash
kubectl apply -f certs/mtls/k8s-mtls-secrets.yaml
```

This creates:
- `mtls-ca` secret in default namespace
- `dogcatcher-server-cert` secret in default namespace
- `kong-client-cert` secret in kong namespace

## Step 3: Deploy Dogcatcher with mTLS

### Update Dogcatcher Deployment

Create or update the Dogcatcher deployment to enable mTLS:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dogcatcher-api
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dogcatcher-api
  template:
    metadata:
      labels:
        app: dogcatcher-api
    spec:
      containers:
        - name: dogcatcher
          image: YOUR_REGISTRY/dogcatcher:latest
          ports:
            - name: http
              containerPort: 5000
            - name: https
              containerPort: 5443
          env:
            - name: MTLS_ENABLED
              value: "false"  # HTTP on port 5000
            - name: API_KEYS
              valueFrom:
                secretKeyRef:
                  name: dogcatcher-api-keys
                  key: api-keys
            - name: API_KEY_REQUIRED
              value: "true"
          volumeMounts:
            - name: certs
              mountPath: /app/certs
              readOnly: true
        # Sidecar for mTLS (gunicorn)
        - name: dogcatcher-mtls
          image: YOUR_REGISTRY/dogcatcher:latest
          command: ["gunicorn", "-c", "gunicorn_mtls.conf.py", "app:app"]
          ports:
            - name: https-mtls
              containerPort: 5443
          env:
            - name: CERT_DIR
              value: "/app/certs"
            - name: API_KEYS
              valueFrom:
                secretKeyRef:
                  name: dogcatcher-api-keys
                  key: api-keys
          volumeMounts:
            - name: certs
              mountPath: /app/certs
              readOnly: true
      volumes:
        - name: certs
          secret:
            secretName: dogcatcher-server-cert
---
apiVersion: v1
kind: Service
metadata:
  name: dogcatcher-api
  namespace: default
spec:
  selector:
    app: dogcatcher-api
  ports:
    - name: http
      port: 5000
      targetPort: 5000
    - name: https
      port: 5443
      targetPort: 5443
```

### Simpler Single Container Approach

Alternatively, run a single container with mTLS only:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dogcatcher-api
spec:
  template:
    spec:
      containers:
        - name: dogcatcher
          image: YOUR_REGISTRY/dogcatcher:latest
          command: ["gunicorn", "-c", "gunicorn_mtls.conf.py", "app:app"]
          ports:
            - containerPort: 5443
          env:
            - name: CERT_DIR
              value: "/app/certs"
          volumeMounts:
            - name: certs
              mountPath: /app/certs
              readOnly: true
      volumes:
        - name: certs
          secret:
            secretName: dogcatcher-server-cert
```

## Step 4: Configure Kong for mTLS Upstream

Run the Kong mTLS configuration script:

```bash
./scripts/configure-kong-mtls.sh

# Or with custom options:
./scripts/configure-kong-mtls.sh \
  --kong-ns kong \
  --dogcatcher-ns default \
  --dogcatcher-svc dogcatcher-api \
  --dogcatcher-port 5443 \
  --cert-dir ./certs/mtls
```

### Manual Kong Configuration

If you prefer manual configuration:

#### 1. Create Kong Secret with Client Certificate

```bash
kubectl create secret generic kong-upstream-mtls \
  --namespace kong \
  --from-file=tls.crt=certs/mtls/kong-client.crt \
  --from-file=tls.key=certs/mtls/kong-client.key \
  --from-file=ca.crt=certs/mtls/ca.crt
```

#### 2. Mount Certificate in Kong Deployment

Update Kong Helm values:

```yaml
# kong-values-mtls.yaml
extraSecretMounts:
  - name: kong-upstream-mtls
    secretName: kong-upstream-mtls
    mountPath: /etc/secrets/kong-upstream-mtls
    readOnly: true

env:
  # Reference certificates for upstream mTLS
  upstream_client_cert: /etc/secrets/kong-upstream-mtls/tls.crt
  upstream_client_key: /etc/secrets/kong-upstream-mtls/tls.key
```

Upgrade Kong:

```bash
helm upgrade kong kong/kong \
  --namespace kong \
  --values kong-values-mtls.yaml
```

#### 3. Create mTLS Service and Ingress

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: dogcatcher-api-mtls
  namespace: default
  annotations:
    konghq.com/protocol: "https"
spec:
  selector:
    app: dogcatcher-api
  ports:
    - port: 5443
      targetPort: 5443
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dogcatcher-mtls
  namespace: default
  annotations:
    konghq.com/plugins: dogcatcher-key-auth
    konghq.com/strip-path: "true"
    konghq.com/protocol: "https"
    # Tell Kong to use client certificate
    konghq.com/client-cert: kong-upstream-mtls
spec:
  ingressClassName: kong
  rules:
    - http:
        paths:
          - path: /dogcatcher-mtls
            pathType: Prefix
            backend:
              service:
                name: dogcatcher-api-mtls
                port:
                  number: 5443
```

## Step 5: Update Model Citizen Configuration

Model Citizen doesn't need to know about mTLS - it just calls Kong:

```yaml
# Helm values for Model Citizen
config:
  # Use mTLS endpoint through Kong
  apiGatewayUrl: "http://kong-kong-proxy.kong.svc.cluster.local/dogcatcher-mtls/api"
  dogcatcherPublicUrl: "https://dogcatcher.example.com"
```

Or for docker-compose:

```yaml
environment:
  API_GATEWAY_URL: http://kong:8000/dogcatcher-mtls/api
```

## Step 6: Testing

### Test mTLS Connection Directly

```bash
# Port-forward to Dogcatcher mTLS port
kubectl port-forward svc/dogcatcher-api 5443:5443

# Test with client certificate
curl --cacert certs/mtls/ca.crt \
     --cert certs/mtls/kong-client.crt \
     --key certs/mtls/kong-client.key \
     https://localhost:5443/api/dogs/

# Test without client certificate (should fail)
curl --cacert certs/mtls/ca.crt \
     https://localhost:5443/api/dogs/
# Expected: SSL handshake error
```

### Test Through Kong

```bash
# Port-forward Kong
kubectl port-forward -n kong svc/kong-kong-proxy 8000:80

# Test mTLS endpoint via Kong
curl http://localhost:8000/dogcatcher-mtls/api/dogs/ \
  -H "X-API-Key: YOUR_API_KEY"
```

### Verify Certificate Chain

```bash
# Check server certificate
openssl s_client -connect localhost:5443 \
  -cert certs/mtls/kong-client.crt \
  -key certs/mtls/kong-client.key \
  -CAfile certs/mtls/ca.crt \
  -verify_return_error

# Verify certificate details
openssl x509 -in certs/mtls/server.crt -text -noout
openssl x509 -in certs/mtls/kong-client.crt -text -noout
```

## Troubleshooting

### SSL Handshake Failures

1. **"certificate verify failed"**: CA certificate not trusted
   - Ensure `ca.crt` is mounted correctly
   - Verify certificate was signed by the CA

2. **"no client certificate"**: Client cert not presented
   - Check Kong secret mount path
   - Verify Kong has access to client certificate

3. **"certificate expired"**: Certificate past validity
   - Regenerate certificates with longer validity

### Check Kong Logs

```bash
kubectl logs -n kong -l app.kubernetes.io/name=kong --tail=100 | grep -i ssl
```

### Check Dogcatcher Logs

```bash
kubectl logs -l app=dogcatcher-api --tail=100 | grep -i ssl
```

### Verify Secrets

```bash
# Check secret exists
kubectl get secret dogcatcher-server-cert -o yaml

# Decode and verify certificate
kubectl get secret dogcatcher-server-cert -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```

## Security Considerations

1. **Protect CA Private Key**: The `ca.key` file can sign any certificate - store securely
2. **Certificate Rotation**: Plan for certificate renewal before expiry
3. **Revocation**: Consider implementing CRL or OCSP for certificate revocation
4. **Network Policies**: Use Kubernetes network policies to restrict access
5. **Secret Management**: Consider using external secret managers (Vault, AWS Secrets Manager)

## Certificate Rotation

When certificates expire:

1. Generate new certificates:
   ```bash
   ./scripts/generate-mtls-certs.sh --output-dir ./certs/mtls-new
   ```

2. Update Kubernetes secrets:
   ```bash
   kubectl apply -f certs/mtls-new/k8s-mtls-secrets.yaml
   ```

3. Restart pods to pick up new certificates:
   ```bash
   kubectl rollout restart deployment dogcatcher-api
   kubectl rollout restart deployment -n kong kong
   ```

## Next Steps

- Implement certificate rotation automation
- Add monitoring for certificate expiry
- Configure network policies for additional security
- Consider service mesh (Istio/Linkerd) for automatic mTLS
