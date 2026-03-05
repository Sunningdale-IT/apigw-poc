"""
Middleware for mTLS client certificate enforcement.

When MTLS_ENABLED=true, gunicorn handles the TLS handshake and client cert
verification at the transport layer (--cert-reqs 2 = ssl.CERT_REQUIRED).
This middleware provides an additional application-layer check that:
  - Confirms the health endpoint is always reachable without a cert
  - Optionally restricts access to clients whose cert CN matches MTLS_REQUIRED_CN
"""
from django.conf import settings
from django.http import JsonResponse


class MtlsClientCertMiddleware:
    """Enforce mTLS client certificate CN restriction at the application layer."""

    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        # Health check endpoint must always be reachable (used by k8s probes on
        # the plain HTTP port, so this middleware will never actually block it,
        # but guard here in case the request arrives on the mTLS port too).
        if request.path in ('/health/', '/health'):
            return self._get_response(request)

        required_cn = getattr(settings, 'MTLS_REQUIRED_CN', '')
        if required_cn:
            # gunicorn exposes the verified peer CN via the SSL_CLIENT_S_DN_CN
            # WSGI environ variable when using --cert-reqs 2.
            client_cn = request.META.get('SSL_CLIENT_S_DN_CN', '')
            if client_cn != required_cn:
                return JsonResponse(
                    {
                        'error': 'mTLS client certificate CN mismatch',
                        'expected': required_cn,
                        'received': client_cn or '(none)',
                    },
                    status=403,
                )

        return self._get_response(request)
