# Let's Encrypt Certificate Setup

This guide covers obtaining and configuring Let's Encrypt TLS certificates for the Dogcatcher API proxy.

## Prerequisites

1. **Domain Name**: A registered domain pointing to your server
2. **Port 80 Access**: Let's Encrypt uses HTTP-01 challenge on port 80
3. **Docker**: Docker and Docker Compose installed
4. **Public IP**: Server must be accessible from the internet

## Quick Start

### 1. Configure DNS

Point your domain to your server's IP address:

```
dogcatcher.example.com  A  YOUR_SERVER_IP
```

Wait for DNS propagation (can take up to 48 hours, usually minutes).

### 2. Start the Proxy

```bash
cd /path/to/apigw-poc
docker compose up -d proxy
```

### 3. Verify HTTP Access

```bash
curl http://dogcatcher.example.com/health
```

### 4. Obtain Certificate

```bash
./scripts/setup-letsencrypt.sh \
  --domain dogcatcher.example.com \
  --email admin@example.com
```

### 5. Test HTTPS

```bash
curl https://dogcatcher.example.com/health
```

## Detailed Setup

### Testing with Staging Environment

Let's Encrypt has rate limits. Use staging for testing:

```bash
./scripts/setup-letsencrypt.sh \
  --domain dogcatcher.example.com \
  --email admin@example.com \
  --staging
```

Staging certificates are not trusted by browsers but work for testing.

### Dry Run

Test the process without obtaining a certificate:

```bash
./scripts/setup-letsencrypt.sh \
  --domain dogcatcher.example.com \
  --email admin@example.com \
  --dry-run
```

### Manual Certificate Obtainment

If you prefer manual control:

```bash
# Run certbot inside the container
docker exec -it dogcatcher-proxy certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@example.com \
  --agree-tos \
  --no-eff-email \
  -d dogcatcher.example.com

# Link certificates
docker exec dogcatcher-proxy ln -sf \
  /etc/letsencrypt/live/dogcatcher.example.com/fullchain.pem \
  /etc/nginx/certs/server.crt

docker exec dogcatcher-proxy ln -sf \
  /etc/letsencrypt/live/dogcatcher.example.com/privkey.pem \
  /etc/nginx/certs/server.key

# Reload nginx
docker exec dogcatcher-proxy nginx -s reload
```

## Certificate Renewal

### Automatic Renewal

The setup script configures automatic renewal via crond:

```bash
# Check renewal cron job
docker exec dogcatcher-proxy cat /etc/periodic/daily/certbot-renew
```

### Manual Renewal

```bash
docker exec dogcatcher-proxy certbot renew

# Or force renewal
docker exec dogcatcher-proxy certbot renew --force-renewal
```

### Test Renewal

```bash
docker exec dogcatcher-proxy certbot renew --dry-run
```

## Multiple Domains

### Subject Alternative Names (SAN)

```bash
docker exec dogcatcher-proxy certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@example.com \
  --agree-tos \
  -d dogcatcher.example.com \
  -d api.example.com \
  -d www.dogcatcher.example.com
```

### Wildcard Certificates

Wildcard certificates require DNS-01 challenge:

```bash
docker exec -it dogcatcher-proxy certbot certonly \
  --manual \
  --preferred-challenges dns \
  -d "*.example.com" \
  -d example.com
```

You'll need to create DNS TXT records as instructed.

## Kubernetes Deployment

For Kubernetes, use cert-manager instead:

### Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### Create ClusterIssuer

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx  # or traefik, kong, etc.
```

### Create Certificate

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: dogcatcher-tls
  namespace: default
spec:
  secretName: dogcatcher-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  commonName: dogcatcher.example.com
  dnsNames:
    - dogcatcher.example.com
```

### Use in Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dogcatcher-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - dogcatcher.example.com
      secretName: dogcatcher-tls-secret
  rules:
    - host: dogcatcher.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: dogcatcher-proxy
                port:
                  number: 80
```

## Troubleshooting

### Check Certificate Status

```bash
docker exec dogcatcher-proxy certbot certificates
```

### View Certificate Details

```bash
docker exec dogcatcher-proxy openssl x509 \
  -in /etc/letsencrypt/live/dogcatcher.example.com/fullchain.pem \
  -text -noout
```

### Check Expiry Date

```bash
docker exec dogcatcher-proxy openssl x509 \
  -in /etc/letsencrypt/live/dogcatcher.example.com/fullchain.pem \
  -enddate -noout
```

### Common Issues

#### 1. "Connection Refused" on Port 80

- Check firewall: `sudo ufw allow 80`
- Check Docker port mapping: `docker ps`
- Verify DNS: `nslookup dogcatcher.example.com`

#### 2. "DNS Problem: NXDOMAIN"

- Domain not pointing to server
- DNS not propagated yet
- Check: `dig dogcatcher.example.com`

#### 3. "Rate Limit Exceeded"

- Too many certificate requests
- Use staging for testing
- Wait and retry (rate limits reset weekly)

#### 4. Certificate Not Trusted

- Using staging certificate
- Re-run without `--staging` flag

#### 5. nginx Doesn't Use New Certificate

```bash
# Check symlinks
docker exec dogcatcher-proxy ls -la /etc/nginx/certs/

# Reload nginx
docker exec dogcatcher-proxy nginx -s reload
```

## Rate Limits

Let's Encrypt has rate limits:

| Limit | Value |
|-------|-------|
| Certificates per domain | 50/week |
| Duplicate certificates | 5/week |
| Failed validations | 5/hour |
| New registrations | 500/3 hours |

Use staging environment for testing to avoid hitting limits.

## Security Best Practices

1. **Use Production Certificates**: Staging certificates are not trusted
2. **Monitor Expiry**: Set up alerts for certificate expiry
3. **Automate Renewal**: Ensure cron/systemd renewal is configured
4. **HSTS**: Consider enabling HTTP Strict Transport Security
5. **OCSP Stapling**: Improve TLS performance

### Enable HSTS

Add to nginx configuration:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Enable OCSP Stapling

```nginx
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

## Backup Certificates

```bash
# Backup Let's Encrypt directory
docker cp dogcatcher-proxy:/etc/letsencrypt ./letsencrypt-backup

# Restore
docker cp ./letsencrypt-backup/. dogcatcher-proxy:/etc/letsencrypt/
```
