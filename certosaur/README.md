# Certosaur 🦖

A small private certificate authority with a web UI, for **testing only**.
Issues root and intermediate CAs, server certificates (with DNS and IP SANs)
and client certificates (PEM plus a password-protected PKCS#12 bundle) for mTLS.

Django + SQLite in one container. Private keys are stored unencrypted in the
database, so never use it for anything real.

## Run it on your laptop

```bash
cd certosaur
docker compose up -d --build
open http://localhost:5003/
```

Login: `admin` / `admin123`.

On first start the entrypoint runs the migrations, creates the admin user and
seeds a CA hierarchy:

| name         | type         | validity |
|--------------|--------------|----------|
| `alpha`      | root         | 20 years |
| `commercial` | intermediate | 10 years |
| `government` | intermediate | 10 years |

## Where the data lives

The SQLite database (CAs, certificates and their private keys) is bind-mounted
from `./data`, and `./certificates_storage` likewise. Both folders are in
`.gitignore` and must stay out of git. Because they are plain folders on your
disk, everything survives `docker compose down`, image rebuilds and a laptop
reboot (`restart: unless-stopped` brings the container back when Docker
Desktop starts). Back them up by copying the folders.

```bash
docker compose logs -f certosaur    # follow the log
docker compose down                 # stop, keep data
docker compose up -d                # start again with the same data
```

## Clean start

To throw everything away and start from a freshly seeded hierarchy:

```bash
CERTOSAUR_CLEAN_START=true docker compose up -d
```

The wipe is one-shot. The entrypoint leaves a marker in `./data`, so a
container restart with the flag still set (for example after a reboot) keeps
the data. The next plain `docker compose up -d` clears the marker, after which
the flag will wipe again. Deleting `./data` and `./certificates_storage` by
hand while the container is stopped does the same thing.

## Settings

All optional, set in the shell or in a `.env` next to `compose.yaml`:

| variable                         | default                                     | meaning |
|----------------------------------|---------------------------------------------|---------|
| `CERTOSAUR_PORT`                 | `5003`                                      | host port |
| `CERTOSAUR_ADMIN_USER`           | `admin`                                     | admin login, created on first start |
| `CERTOSAUR_ADMIN_PASSWORD`       | `admin123`                                  | admin password, created on first start |
| `CERTOSAUR_SEED_CAS`             | `true`                                      | seed alpha/commercial/government when the database has no CA |
| `CERTOSAUR_CLEAN_START`          | `false`                                     | wipe all data once at startup, see Clean start |
| `CERTOSAUR_DATA_DIR`             | `./data`                                    | host folder for the database |
| `CERTOSAUR_CERTS_DIR`            | `./certificates_storage`                    | host folder for stored certificate files |
| `CERTOSAUR_SECRET_KEY`           | dev value                                   | Django `SECRET_KEY` |
| `DJANGO_DEBUG`                   | `false`                                     | Django debug mode |
| `CERTOSAUR_ALLOWED_HOSTS`        | `localhost,127.0.0.1,certosaur,host.docker.internal` | comma-separated `ALLOWED_HOSTS` |
| `CERTOSAUR_CSRF_TRUSTED_ORIGINS` | `http://localhost:5003,http://127.0.0.1:5003` | add your origin here if you change the port or put it behind a proxy, otherwise forms return 403 |

Changing the port means changing both `CERTOSAUR_PORT` and
`CERTOSAUR_CSRF_TRUSTED_ORIGINS`.

## Using the certificates

Every CA, server and client certificate has download links on its detail page
(login required):

- CA: `/ca/<id>/download/cert/` and `/download/key/`
- Server: `/server/<id>/download/cert/`, `/key/`, `/chain/` (leaf + issuing
  intermediate, in that order, ready for a web server's `fullchain`)
- Client: `/client/<id>/download/cert/`, `/key/`, `/p12/` (password shown on
  the detail page)

To trust what Certosaur issues, install the **root** CA certificate
(`alpha-ca.crt`) in the client's trust store, and serve the chain file on the
server side. Verify a server certificate by hand with:

```bash
openssl verify -CAfile alpha-ca.crt -untrusted hello.example-fullchain.crt hello.example.crt
```

## Without compose

```bash
docker build -t certosaur:local .
docker run -d --name certosaur -p 5003:8000 --restart unless-stopped \
  -v "$PWD/data:/app/data" -v "$PWD/certificates_storage:/app/certificates_storage" \
  -e DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5003 \
  certosaur:local
```

## Notes

- `/health/` is unauthenticated and used by the container healthcheck.
- The image also runs in Kubernetes; see `helm-chart/citizen-suite/charts/certosaur`.
  The Postgres variables that chart passes are ignored: storage is SQLite on
  the `/app/data` volume.
