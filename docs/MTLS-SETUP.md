# Mutual TLS (mTLS) Setup Guide

This guide explains how to configure mutual TLS between the Producer (3rd party) and Consumer (home party) services through Kong API Gateway.

> **See Also**: [MTLS-REAL-WORLD-GUIDE.md](MTLS-REAL-WORLD-GUIDE.md) for real-world negotiation steps, certificate exchange processes, and Kong benefits scenarios.

## Overview

```
┌─────────────────┐         ┌──────────────────────────┐         ┌─────────────────┐
│                 │  mTLS   │                          │  HTTP   │                 │
│    Producer     │────────►│     Kong API Gateway     │────────►│    Consumer     │
│   (3rd Party)   │         │      (Home Party)        │         │   (Internal)    │
│                 │         │                          │         │                 │
└─────────────────┘         └──────────────────────────┘         └─────────────────┘
     Client Cert                   Validates Cert                   Backend Service
```

**Terminology:**
- **Home Party (Consumer)**: Owns and operates Kong API Gateway. Internal services are trusted.
- **3rd Party (Producer)**: External service that must authenticate using a client certificate.

## Architecture

1. **Private CA**: A cert-manager `ClusterIssuer` or `Issuer` creates a private Certificate Authority for mTLS
2. **Kong mTLS**: Kong is configured to require client certificates on specific routes
3. **Client Certificates**: Issued to 3rd parties (like Producer) for authentication
4. **Certificate Validation**: Kong validates client certificates against the CA

## Prerequisites

- Kubernetes cluster with cert-manager installed
- Helm chart deployed (`apigw-poc`)
- `kubectl` and `helm` CLI tools

Verify cert-manager is running:
```bash
kubectl get pods -n cert-manager
```

## Step 1: Create the mTLS Certificate Authority

Create a self-signed CA issuer for mTLS certificates.

```bash
kubectl apply -f k8s-manifests/mtls/01-mtls-ca.yaml
```

This creates:
- A self-signed `ClusterIssuer` for bootstrapping
- A CA certificate in the `apigw-poc` namespace
- A `ClusterIssuer` that uses this CA to issue mTLS certificates

## Step 2: Issue Client Certificate for Producer (3rd Party)

Issue a client certificate for the Producer service:

```bash
kubectl apply -f k8s-manifests/mtls/02-producer-client-cert.yaml
```

This creates a `Certificate` resource that cert-manager will fulfill, storing the certificate and key in a Kubernetes Secret.

## Step 3: Configure Kong for mTLS (Optional - Enforcement)

> **Note**: Steps 1-2 create the certificate infrastructure. Step 3 is optional and enables Kong to **require** client certificates on specific routes.

To enforce mTLS (reject requests without valid client certificates):

```bash
kubectl apply -f k8s-manifests/mtls/03-kong-mtls-config.yaml
```

This patches Kong to mount the CA certificate for client validation.

### Kong mTLS Plugin Configuration

Kong OSS supports the `mtls-auth` plugin for client certificate validation. Add this to your Kong declarative config:

```yaml
plugins:
  - name: mtls-auth
    route: consumer-route
    config:
      ca_certificates:
        - <CA-CERTIFICATE-ID>
      skip_consumer_lookup: true
```

For Kong OSS without the mtls-auth plugin, you can use Traefik or Nginx ingress to handle mTLS at the ingress level.

## Step 4: Enable mTLS Enforcement (Traefik)

Since this PoC uses Traefik as the ingress controller, mTLS enforcement is configured at the Traefik level.

**Important**: Traefik requires all routes on the same host to use the same TLS options. Therefore, mTLS-protected routes use a dedicated subdomain:

| Endpoint | URL | mTLS Required |
|----------|-----|---------------|
| Standard | `https://kong.jim00.pd.test-rig.nl/*` | No |
| mTLS-Protected | `https://kong-mtls.jim00.pd.test-rig.nl/*` | Yes |

### Enable mTLS Enforcement

```bash
# Apply Traefik mTLS configuration
kubectl apply -f k8s-manifests/mtls/04-traefik-mtls-enforcement.yaml
```

This:
- Creates a `TLSOption` requiring client certificates
- Creates `IngressRoute` for `kong-mtls.*` with mTLS enabled
- Issues a TLS certificate for the mTLS subdomain

### Verify Enforcement

```bash
# Test WITHOUT certificate on mTLS endpoint (should fail - TLS handshake error)
curl https://kong-mtls.jim00.pd.test-rig.nl/consumer/api/consume

# Test WITH certificate on mTLS endpoint (should succeed)
curl --cert ./certs/client.crt --key ./certs/client.key --cacert ./certs/ca.crt \
  https://kong-mtls.jim00.pd.test-rig.nl/consumer/api/consume

# Or use the test script
./scripts/test-mtls.sh --all
```

### Disable Enforcement

```bash
kubectl delete -f k8s-manifests/mtls/04-traefik-mtls-enforcement.yaml
```

## Step 5: Test the mTLS Connection

### Test WITHOUT Client Certificate (Should Fail)

```bash
./scripts/test-mtls.sh --no-cert
```

Expected: `400 Bad Request` or `SSL certificate problem`

### Test WITH Client Certificate (Should Succeed)

```bash
./scripts/test-mtls.sh --with-cert
```

Expected: Successful response from Consumer service

## Certificate Management

### View Issued Certificates

```bash
kubectl get certificates -n apigw-poc
kubectl get secrets -n apigw-poc | grep tls
```

### Renew a Certificate

cert-manager automatically renews certificates before expiry. To force renewal:

```bash
kubectl delete secret producer-mtls-client-cert -n apigw-poc
# cert-manager will automatically re-issue
```

### Revoke a Certificate (Remove Access)

To revoke access for a 3rd party, delete their certificate:

```bash
kubectl delete certificate producer-mtls-client -n apigw-poc
kubectl delete secret producer-mtls-client-cert -n apigw-poc
```

## Adding New 3rd Party Clients

To add a new 3rd party that needs API access:

1. Create a new Certificate resource:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: new-partner-mtls-client
  namespace: apigw-poc
spec:
  secretName: new-partner-mtls-client-cert
  duration: 8760h  # 1 year
  renewBefore: 720h  # 30 days
  subject:
    organizations:
      - "New Partner Inc"
  commonName: "new-partner-client"
  usages:
    - client auth
  issuerRef:
    name: mtls-ca-issuer
    kind: ClusterIssuer
```

2. Extract the certificate for the partner:

```bash
./scripts/extract-client-cert.sh new-partner-mtls-client-cert
```

3. Provide the extracted files to the partner:
   - `client.crt` - Client certificate
   - `client.key` - Private key
   - `ca.crt` - CA certificate (for server verification)

## Troubleshooting

### Certificate Not Ready

```bash
kubectl describe certificate producer-mtls-client -n apigw-poc
kubectl describe certificaterequest -n apigw-poc
```

### Kong Not Validating Certificates

Check Kong logs:
```bash
kubectl logs -n apigw-poc deployment/kong-proxy | grep -i ssl
```

Verify CA is mounted:
```bash
kubectl exec -n apigw-poc deployment/kong-proxy -- cat /etc/kong/mtls/ca.crt
```

### Client Connection Refused

Verify the client certificate:
```bash
openssl x509 -in client.crt -text -noout
openssl verify -CAfile ca.crt client.crt
```

## Security Considerations

1. **Private Key Protection**: Client private keys should never be transmitted insecurely
2. **Certificate Rotation**: Use short-lived certificates (e.g., 90 days) with automatic renewal
3. **Revocation**: Implement a process to quickly revoke compromised certificates
4. **Audit Logging**: Enable Kong's logging plugin to track mTLS authentication events
5. **Network Policies**: Combine mTLS with Kubernetes NetworkPolicies for defense in depth

## File Reference

| File | Description |
|------|-------------|
| `k8s-manifests/mtls/01-mtls-ca.yaml` | CA issuer configuration |
| `k8s-manifests/mtls/02-producer-client-cert.yaml` | Producer client certificate |
| `k8s-manifests/mtls/03-kong-mtls-config.yaml` | Kong mTLS configuration |
| `scripts/test-mtls.sh` | mTLS connection test script |
| `scripts/extract-client-cert.sh` | Extract certs from K8s secrets |
