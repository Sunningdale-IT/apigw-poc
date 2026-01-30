# Gunicorn configuration for mTLS
# Usage: gunicorn -c gunicorn_mtls.conf.py app:app

import os
import ssl

# Server socket
bind = '0.0.0.0:5443'
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# SSL/TLS Configuration for mTLS
cert_dir = os.environ.get('CERT_DIR', '/app/certs')

certfile = os.environ.get('SERVER_CERT', f'{cert_dir}/server.crt')
keyfile = os.environ.get('SERVER_KEY', f'{cert_dir}/server.key')
ca_certs = os.environ.get('CA_CERT', f'{cert_dir}/ca.crt')

# Require client certificate (mTLS)
cert_reqs = ssl.CERT_REQUIRED

# SSL protocol version
ssl_version = ssl.PROTOCOL_TLS_SERVER

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Process naming
proc_name = 'dogcatcher-mtls'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Print config on startup
def on_starting(server):
    print("=" * 60)
    print("Dogcatcher API - mTLS Mode")
    print("=" * 60)
    print(f"Bind: {bind}")
    print(f"Workers: {workers}")
    print(f"Server Certificate: {certfile}")
    print(f"Server Key: {keyfile}")
    print(f"CA Certificate: {ca_certs}")
    print(f"Client Cert Required: Yes (mTLS)")
    print("=" * 60)
