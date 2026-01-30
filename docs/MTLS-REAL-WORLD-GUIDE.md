# Mutual TLS: Real-World Implementation Guide

This document describes the real-world process of establishing mutual TLS (mTLS) between two organizations and demonstrates how Kong API Gateway provides value in this scenario.

## Table of Contents

1. [Parties Involved](#parties-involved)
2. [Real-World Negotiation Steps](#real-world-negotiation-steps)
3. [Certificate Exchange Process](#certificate-exchange-process)
4. [Kong API Gateway Benefits](#kong-api-gateway-benefits)
5. [Demonstration Scenarios](#demonstration-scenarios)

---

## Parties Involved

| Party | Role | Description |
|-------|------|-------------|
| **Home Party (Consumer)** | API Provider | Owns and operates the Kong API Gateway. Exposes internal APIs to trusted partners. |
| **3rd Party (Producer)** | API Consumer | External organization that needs access to the Home Party's APIs. Must authenticate using client certificates. |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NETWORK BOUNDARY                                   │
│                                                                              │
│  ┌──────────────────────┐                    ┌──────────────────────────┐   │
│  │   3rd Party Org      │                    │      Home Party Org      │   │
│  │   (Producer)         │                    │      (Consumer)          │   │
│  │                      │     mTLS           │                          │   │
│  │  ┌────────────────┐  │  ┌──────────┐     │  ┌──────────────────────┐│   │
│  │  │ Producer App   │──┼──│  Kong    │─────┼──│    Consumer API      ││   │
│  │  │                │  │  │ Gateway  │     │  │                      ││   │
│  │  │ Uses:          │  │  │          │     │  │  Internal service    ││   │
│  │  │ - Client Cert  │  │  │ Validates│     │  │  exposed via Kong    ││   │
│  │  │ - Private Key  │  │  │ - Certs  │     │  │                      ││   │
│  │  └────────────────┘  │  │ - Routes │     │  └──────────────────────┘│   │
│  │                      │  │ - Rate   │     │                          │   │
│  │                      │  │   Limits │     │                          │   │
│  └──────────────────────┘  └──────────┘     └──────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Real-World Negotiation Steps

### Phase 1: Business Agreement (Week 1-2)

1. **Initial Contact**
   - 3rd Party requests API access to Home Party's services
   - Business teams negotiate terms, SLAs, and data sharing agreements

2. **Security Requirements Review**
   - Home Party shares API security documentation
   - Both parties agree on authentication method (mTLS)
   - Data classification and handling requirements established

3. **Technical Contact Exchange**
   - Each organization designates a technical point of contact
   - Communication channels established (encrypted email, secure portal)

### Phase 2: Certificate Infrastructure Setup (Week 2-3)

4. **Certificate Authority (CA) Decision**
   
   | Option | Pros | Cons |
   |--------|------|------|
   | **Home Party's Private CA** | Full control, no cost | 3rd Party must trust new CA |
   | **3rd Party's CA** | 3rd Party manages own certs | Home Party must trust external CA |
   | **Public CA** | Universally trusted | Less control, may expose org structure |
   | **Mutual Private CAs** | Maximum control | Complex, both sides need CA infrastructure |

   **Recommended**: Home Party operates Private CA for mTLS (this PoC uses this approach)

5. **CA Certificate Exchange**
   ```
   Home Party → 3rd Party:
   - CA Certificate (public) for server verification
   - Certificate requirements document
   - API endpoint documentation
   
   3rd Party → Home Party:
   - Organization details for certificate subject
   - Technical contact for certificate delivery
   - IP ranges (if IP allowlisting is used)
   ```

### Phase 3: Certificate Issuance (Week 3)

6. **Certificate Signing Request (CSR) - Option A: 3rd Party generates**
   ```bash
   # 3rd Party generates private key (NEVER shares this)
   openssl ecparam -genkey -name prime256v1 -out producer-client.key
   
   # 3rd Party generates CSR
   openssl req -new -key producer-client.key \
     -out producer-client.csr \
     -subj "/O=Producer Organization/OU=Integration Team/CN=producer-api-client"
   
   # 3rd Party sends CSR to Home Party (CSR contains NO private data)
   ```

7. **Certificate Signing Request - Option B: Home Party generates (this PoC)**
   ```bash
   # Home Party generates both key and certificate using cert-manager
   # Key and certificate delivered securely to 3rd Party
   ```

8. **Certificate Delivery**
   ```
   Home Party → 3rd Party (via secure channel):
   - Signed client certificate (client.crt)
   - Private key (client.key) - ONLY if Home Party generated it
   - CA certificate (ca.crt) for chain verification
   - Certificate expiration date and renewal process
   ```

### Phase 4: Integration Testing (Week 4)

9. **Test Environment Validation**
   - 3rd Party configures their client with certificates
   - Initial connection tests against Home Party's test environment
   - Both parties verify logging and monitoring

10. **Production Cutover**
    - Certificates rotated to production-specific ones (if separate)
    - DNS and firewall rules updated
    - Monitoring alerts configured

### Phase 5: Ongoing Operations

11. **Certificate Lifecycle Management**
    - Automated renewal reminders (30 days before expiry)
    - Revocation procedures documented
    - Annual security review

---

## Certificate Exchange Process

### Secure Exchange Methods

| Method | Security Level | Use Case |
|--------|---------------|----------|
| Encrypted Email (PGP/S-MIME) | Medium | Initial exchange |
| Secure File Transfer (SFTP) | High | Certificate delivery |
| Hardware Security Module (HSM) | Very High | Enterprise environments |
| In-Person Exchange | Maximum | Highly sensitive integrations |

### What Gets Exchanged

```
┌─────────────────────────────────────────────────────────────────┐
│                    CERTIFICATE EXCHANGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Home Party PROVIDES to 3rd Party:                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✓ CA Certificate (ca.crt)        - Public, for trust    │    │
│  │ ✓ Client Certificate (client.crt) - Public, identity    │    │
│  │ ✓ Client Private Key (client.key) - SECRET!             │    │
│  │   (Only if Home Party generated the key pair)            │    │
│  │ ✓ API Documentation              - Endpoints, formats   │    │
│  │ ✓ Kong Gateway URL               - Where to connect     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  3rd Party PROVIDES to Home Party:                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✓ Organization Details           - For cert subject     │    │
│  │ ✓ CSR (if they generate key)     - Certificate request  │    │
│  │ ✓ Source IP Ranges (optional)    - For IP allowlisting  │    │
│  │ ✓ Technical Contact              - For support          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  NEVER EXCHANGED:                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✗ CA Private Key                 - Only Home Party has  │    │
│  │ ✗ Client Private Key             - Only 3rd Party has   │    │
│  │   (unless Home Party generated it for them)              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Kong API Gateway Benefits

### Scenario 1: Centralized Authentication

**Without Kong:**
- Each internal service must implement mTLS validation
- Certificate validation code duplicated across services
- Difficult to maintain consistent security policies

**With Kong:**
- mTLS handled at the gateway level
- Internal services receive pre-authenticated requests
- Single point of certificate validation

```
Without Kong:
  Client → Service A (mTLS) → Database
  Client → Service B (mTLS) → Database
  Client → Service C (mTLS) → Database
  (3 implementations of mTLS)

With Kong:
  Client → Kong (mTLS) → Service A → Database
                      → Service B → Database
                      → Service C → Database
  (1 implementation of mTLS)
```

### Scenario 2: Rate Limiting per Partner

**Business Value:** Different partners have different SLAs

```yaml
# Kong Configuration
plugins:
  - name: rate-limiting
    consumer: partner-a
    config:
      minute: 1000
      policy: local
  
  - name: rate-limiting
    consumer: partner-b
    config:
      minute: 100
      policy: local
```

### Scenario 3: Request Transformation

**Business Value:** 3rd parties use different data formats

```yaml
# Kong transforms legacy XML to internal JSON
plugins:
  - name: request-transformer
    config:
      add:
        headers:
          - "Content-Type: application/json"
      replace:
        body: "{{ xml_to_json(request.body) }}"
```

### Scenario 4: Audit Logging

**Business Value:** Compliance requires logging all 3rd party access

```yaml
plugins:
  - name: http-log
    config:
      http_endpoint: "https://siem.homeorg.com/kong-logs"
      method: POST
      content_type: application/json
```

### Scenario 5: Circuit Breaker

**Business Value:** Protect internal services from 3rd party traffic spikes

```yaml
plugins:
  - name: proxy-cache
    config:
      strategy: memory
      cache_ttl: 300
  
  - name: request-termination
    config:
      status_code: 503
      message: "Service temporarily unavailable"
    # Activated when backend is unhealthy
```

### Scenario 6: API Versioning

**Business Value:** Support multiple API versions for different partners

```yaml
services:
  - name: consumer-v1
    url: http://consumer-v1-service:80
    routes:
      - paths: ["/v1/consumer"]
  
  - name: consumer-v2
    url: http://consumer-v2-service:80
    routes:
      - paths: ["/v2/consumer"]
```

### Scenario 7: Partner Onboarding/Offboarding

**Business Value:** Quickly add or remove partner access

```bash
# Onboard new partner
kubectl apply -f partner-certificate.yaml
# Kong automatically picks up new cert from CA

# Offboard partner (immediate revocation)
kubectl delete certificate partner-x-cert -n apigw-poc
# Kong rejects subsequent requests
```

---

## Demonstration Scenarios

### Demo 1: Successful mTLS Connection

```bash
# Producer (3rd Party) calls Consumer (Home Party) API through Kong
./scripts/test-mtls.sh --with-cert

# Expected: 200 OK with response data
```

### Demo 2: Rejected Connection (No Certificate)

```bash
# Request without client certificate
curl https://kong.jim00.pd.test-rig.nl/consumer/api/consume

# Expected: 400 Bad Request (when mTLS enforced)
# "No required SSL certificate was sent"
```

### Demo 3: Rejected Connection (Invalid Certificate)

```bash
# Request with self-signed certificate (not from trusted CA)
openssl req -x509 -newkey rsa:2048 -keyout fake.key -out fake.crt -days 1 -nodes -subj "/CN=fake"
curl --cert fake.crt --key fake.key https://kong.jim00.pd.test-rig.nl/consumer/api/consume

# Expected: 400 Bad Request
# "SSL certificate problem: unable to get local issuer certificate"
```

### Demo 4: Rejected Connection (Expired Certificate)

```bash
# Create an already-expired certificate for testing
# (In real life, this happens when certificates aren't renewed)

# Expected: 400 Bad Request
# "SSL certificate has expired"
```

### Demo 5: Certificate Revocation

```bash
# Revoke a partner's access
kubectl delete certificate producer-mtls-client -n apigw-poc
kubectl delete secret producer-mtls-client-cert -n apigw-poc

# Attempt to connect with revoked certificate
./scripts/test-mtls.sh --with-cert

# Expected: 401 Unauthorized or connection refused
```

---

## Quick Reference

### Commands for Home Party (Certificate Issuer)

```bash
# Setup mTLS infrastructure
./scripts/setup-mtls.sh

# Issue certificate for new partner
kubectl apply -f k8s-manifests/mtls/partner-cert.yaml

# Extract certificates for partner
./scripts/extract-client-cert.sh partner-mtls-client-cert ./partner-certs

# Revoke partner access
kubectl delete certificate partner-mtls-client -n apigw-poc

# View all issued certificates
kubectl get certificates -n apigw-poc
```

### Commands for 3rd Party (Certificate User)

```bash
# Test connection with certificate
curl --cert client.crt --key client.key --cacert ca.crt \
  https://kong.jim00.pd.test-rig.nl/consumer/api/consume

# Verify certificate validity
openssl x509 -in client.crt -noout -dates

# Check certificate chain
openssl verify -CAfile ca.crt client.crt
```

---

## Security Checklist

- [ ] Private keys are never transmitted over unencrypted channels
- [ ] Certificates have appropriate validity periods (90 days recommended)
- [ ] Automated renewal is configured (cert-manager handles this)
- [ ] Certificate revocation process is documented and tested
- [ ] Audit logging is enabled for all mTLS connections
- [ ] IP allowlisting is considered as additional security layer
- [ ] Rate limiting is configured per partner
- [ ] Incident response procedures are documented
