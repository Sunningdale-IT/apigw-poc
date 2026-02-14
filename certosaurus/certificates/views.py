"""
Views for Certosaurus certificate management portal. 🦖
RAWR! Let's make some certificates!
"""

import base64
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import CertificateAuthority, ServerCertificate, ClientCertificate
from .forms import (
    LoginForm, CertificateAuthorityForm, ServerCertificateForm,
    ClientCertificateForm, RevokeCertificateForm
)
from .cert_utils import (
    generate_ca_certificate, generate_server_certificate,
    generate_client_certificate, create_p12_bundle,
    serialize_certificate, serialize_private_key,
    load_certificate_from_pem, load_private_key_from_pem,
    generate_random_password
)


@csrf_exempt
def health(request):
    """Health check endpoint for Kubernetes probes."""
    return JsonResponse({'status': 'healthy', 'service': 'certosaurus'})


def index(request):
    """Home page with dashboard."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get counts for dashboard
    ca_count = CertificateAuthority.objects.count()
    server_cert_count = ServerCertificate.objects.filter(status='active').count()
    client_cert_count = ClientCertificate.objects.filter(status='active').count()
    
    # Get recent certificates
    recent_cas = CertificateAuthority.objects.all()[:5]
    recent_server_certs = ServerCertificate.objects.all()[:5]
    recent_client_certs = ClientCertificate.objects.all()[:5]
    
    # Get expiring soon (within 30 days)
    from django.utils import timezone
    from datetime import timedelta
    
    soon = timezone.now() + timedelta(days=30)
    expiring_server = ServerCertificate.objects.filter(
        status='active',
        valid_until__lte=soon,
        valid_until__gte=timezone.now()
    )
    expiring_client = ClientCertificate.objects.filter(
        status='active',
        valid_until__lte=soon,
        valid_until__gte=timezone.now()
    )
    
    context = {
        'ca_count': ca_count,
        'server_cert_count': server_cert_count,
        'client_cert_count': client_cert_count,
        'recent_cas': recent_cas,
        'recent_server_certs': recent_server_certs,
        'recent_client_certs': recent_client_certs,
        'expiring_server': expiring_server,
        'expiring_client': expiring_client,
    }
    return render(request, 'dashboard.html', context)


def login_view(request):
    """User login page."""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'RAWR! Welcome to Certosaurus! 🦖')
            return redirect('index')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, 'You have left the Jurassic zone. See you soon! 🦕')
    return redirect('login')


# Certificate Authority Views

@login_required
def ca_list(request):
    """List all Certificate Authorities."""
    cas = CertificateAuthority.objects.all()
    return render(request, 'ca/list.html', {'cas': cas})


@login_required
def ca_create(request):
    """Create a new Certificate Authority."""
    if request.method == 'POST':
        form = CertificateAuthorityForm(request.POST)
        if form.is_valid():
            ca = form.save(commit=False)
            ca.created_by = request.user
            
            validity_days = form.cleaned_data['validity_days']
            key_size = int(form.cleaned_data['key_size'])
            
            # Generate the CA certificate
            parent_ca = form.cleaned_data.get('parent_ca')
            parent_cert = None
            parent_key = None
            
            if parent_ca:
                ca.is_root = False
                parent_cert = load_certificate_from_pem(parent_ca.certificate_pem)
                parent_key = load_private_key_from_pem(parent_ca.private_key_pem)
            else:
                ca.is_root = True
            
            cert, private_key = generate_ca_certificate(
                common_name=ca.common_name,
                organization=ca.organization,
                organizational_unit=ca.organizational_unit,
                country=ca.country,
                state=ca.state,
                locality=ca.locality,
                validity_days=validity_days,
                key_size=key_size,
                parent_cert=parent_cert,
                parent_key=parent_key,
            )
            
            ca.certificate_pem = serialize_certificate(cert).decode()
            ca.private_key_pem = serialize_private_key(private_key).decode()
            ca.valid_from = cert.not_valid_before_utc
            ca.valid_until = cert.not_valid_after_utc
            ca.save()
            
            messages.success(request, f'RAWR! Certificate Authority "{ca.name}" hatched successfully! 🥚🦖')
            return redirect('ca_detail', pk=ca.pk)
    else:
        form = CertificateAuthorityForm()
    
    return render(request, 'ca/create.html', {'form': form})


@login_required
def ca_detail(request, pk):
    """View Certificate Authority details."""
    ca = get_object_or_404(CertificateAuthority, pk=pk)
    server_certs = ca.server_certificates.all()[:10]
    client_certs = ca.client_certificates.all()[:10]
    child_cas = ca.child_cas.all()
    
    context = {
        'ca': ca,
        'server_certs': server_certs,
        'client_certs': client_certs,
        'child_cas': child_cas,
    }
    return render(request, 'ca/detail.html', context)


@login_required
def ca_download(request, pk, file_type):
    """Download CA certificate or key."""
    ca = get_object_or_404(CertificateAuthority, pk=pk)
    
    if file_type == 'cert':
        response = HttpResponse(ca.certificate_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{ca.name}-ca.crt"'
    elif file_type == 'key':
        response = HttpResponse(ca.private_key_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{ca.name}-ca.key"'
    else:
        return HttpResponse('Invalid file type', status=400)
    
    return response


@login_required
@require_POST
def ca_delete(request, pk):
    """Delete a Certificate Authority."""
    ca = get_object_or_404(CertificateAuthority, pk=pk)
    
    # Check for dependencies
    server_count = ca.server_certificates.count()
    client_count = ca.client_certificates.count()
    child_count = ca.child_cas.count()
    
    if server_count > 0 or client_count > 0 or child_count > 0:
        messages.error(
            request, 
            f'Cannot delete CA "{ca.name}" - it has {server_count} server certs, '
            f'{client_count} client certs, and {child_count} child CAs. '
            f'Delete or revoke these first! ☄️'
        )
        return redirect('ca_detail', pk=pk)
    
    ca_name = ca.name
    ca.delete()
    messages.success(request, f'CA "{ca_name}" has gone extinct! 🦴')
    return redirect('ca_list')


# Server Certificate Views

@login_required
def server_cert_list(request):
    """List all Server Certificates."""
    certs = ServerCertificate.objects.all()
    return render(request, 'server/list.html', {'certs': certs})


@login_required
def server_cert_create(request):
    """Create a new Server Certificate."""
    if not CertificateAuthority.objects.exists():
        messages.warning(request, 'You need to hatch a Certificate Authority first! 🥚')
        return redirect('ca_create')
    
    if request.method == 'POST':
        form = ServerCertificateForm(request.POST)
        if form.is_valid():
            cert_obj = form.save(commit=False)
            cert_obj.created_by = request.user
            
            validity_days = form.cleaned_data['validity_days']
            ca = cert_obj.issuing_ca
            
            # Load CA certificate and key
            ca_cert = load_certificate_from_pem(ca.certificate_pem)
            ca_key = load_private_key_from_pem(ca.private_key_pem)
            
            # Parse SANs
            san_dns = cert_obj.get_san_dns_list()
            san_ips = cert_obj.get_san_ip_list()
            
            # Generate the certificate
            cert, private_key = generate_server_certificate(
                common_name=cert_obj.common_name,
                ca_cert=ca_cert,
                ca_key=ca_key,
                san_dns_names=san_dns,
                san_ip_addresses=san_ips,
                organization=cert_obj.organization,
                organizational_unit=cert_obj.organizational_unit,
                country=cert_obj.country,
                state=cert_obj.state,
                locality=cert_obj.locality,
                validity_days=validity_days,
                key_size=cert_obj.key_size,
            )
            
            cert_obj.certificate_pem = serialize_certificate(cert).decode()
            cert_obj.private_key_pem = serialize_private_key(private_key).decode()
            cert_obj.certificate_chain_pem = cert_obj.certificate_pem + ca.certificate_pem
            cert_obj.valid_from = cert.not_valid_before_utc
            cert_obj.valid_until = cert.not_valid_after_utc
            cert_obj.status = 'active'
            cert_obj.save()
            
            messages.success(request, f'CHOMP! Server Certificate "{cert_obj.name}" created! 🦖🔒')
            return redirect('server_cert_detail', pk=cert_obj.pk)
    else:
        form = ServerCertificateForm()
    
    return render(request, 'server/create.html', {'form': form})


@login_required
def server_cert_detail(request, pk):
    """View Server Certificate details."""
    cert = get_object_or_404(ServerCertificate, pk=pk)
    return render(request, 'server/detail.html', {'cert': cert})


@login_required
def server_cert_download(request, pk, file_type):
    """Download Server Certificate files."""
    cert = get_object_or_404(ServerCertificate, pk=pk)
    
    if file_type == 'cert':
        response = HttpResponse(cert.certificate_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{cert.common_name}.crt"'
    elif file_type == 'key':
        response = HttpResponse(cert.private_key_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{cert.common_name}.key"'
    elif file_type == 'chain':
        response = HttpResponse(cert.certificate_chain_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{cert.common_name}-fullchain.crt"'
    else:
        return HttpResponse('Invalid file type', status=400)
    
    return response


@login_required
@require_POST
def server_cert_revoke(request, pk):
    """Revoke a Server Certificate."""
    cert = get_object_or_404(ServerCertificate, pk=pk)
    form = RevokeCertificateForm(request.POST)
    
    if form.is_valid():
        from django.utils import timezone
        cert.status = 'revoked'
        cert.revoked_at = timezone.now()
        cert.revocation_reason = form.cleaned_data['reason']
        cert.save()
        messages.success(request, f'Certificate "{cert.name}" went extinct! 🦴')
    
    return redirect('server_cert_detail', pk=pk)


@login_required
@require_POST
def server_cert_delete(request, pk):
    """Delete a Server Certificate."""
    cert = get_object_or_404(ServerCertificate, pk=pk)
    cert_name = cert.name
    cert.delete()
    messages.success(request, f'Server certificate "{cert_name}" has been deleted! 🦴')
    return redirect('server_cert_list')


# Client Certificate Views

@login_required
def client_cert_list(request):
    """List all Client Certificates."""
    certs = ClientCertificate.objects.all()
    return render(request, 'client/list.html', {'certs': certs})


@login_required
def client_cert_create(request):
    """Create a new Client Certificate."""
    if not CertificateAuthority.objects.exists():
        messages.warning(request, 'You need to hatch a Certificate Authority first! 🥚')
        return redirect('ca_create')
    
    if request.method == 'POST':
        form = ClientCertificateForm(request.POST)
        if form.is_valid():
            cert_obj = form.save(commit=False)
            cert_obj.created_by = request.user
            
            validity_days = form.cleaned_data['validity_days']
            generate_p12 = form.cleaned_data.get('generate_p12', True)
            ca = cert_obj.issuing_ca
            
            # Load CA certificate and key
            ca_cert = load_certificate_from_pem(ca.certificate_pem)
            ca_key = load_private_key_from_pem(ca.private_key_pem)
            
            # Generate the certificate
            cert, private_key = generate_client_certificate(
                common_name=cert_obj.common_name,
                ca_cert=ca_cert,
                ca_key=ca_key,
                email=cert_obj.email,
                organization=cert_obj.organization,
                organizational_unit=cert_obj.organizational_unit,
                country=cert_obj.country,
                state=cert_obj.state,
                locality=cert_obj.locality,
                validity_days=validity_days,
                key_size=cert_obj.key_size,
            )
            
            cert_obj.certificate_pem = serialize_certificate(cert).decode()
            cert_obj.private_key_pem = serialize_private_key(private_key).decode()
            cert_obj.valid_from = cert.not_valid_before_utc
            cert_obj.valid_until = cert.not_valid_after_utc
            cert_obj.status = 'active'
            
            # Generate PKCS#12 bundle
            if generate_p12:
                p12_password = generate_random_password()
                p12_data = create_p12_bundle(
                    certificate=cert,
                    private_key=private_key,
                    ca_cert=ca_cert,
                    password=p12_password,
                    friendly_name=cert_obj.name,
                )
                cert_obj.p12_bundle = p12_data
                cert_obj.p12_password = p12_password
            
            cert_obj.save()
            
            messages.success(request, f'STOMP! Client Certificate "{cert_obj.name}" created! 🦕🎫')
            return redirect('client_cert_detail', pk=cert_obj.pk)
    else:
        form = ClientCertificateForm()
    
    return render(request, 'client/create.html', {'form': form})


@login_required
def client_cert_detail(request, pk):
    """View Client Certificate details."""
    cert = get_object_or_404(ClientCertificate, pk=pk)
    return render(request, 'client/detail.html', {'cert': cert})


@login_required
def client_cert_download(request, pk, file_type):
    """Download Client Certificate files."""
    cert = get_object_or_404(ClientCertificate, pk=pk)
    
    if file_type == 'cert':
        response = HttpResponse(cert.certificate_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{cert.common_name}.crt"'
    elif file_type == 'key':
        response = HttpResponse(cert.private_key_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = f'attachment; filename="{cert.common_name}.key"'
    elif file_type == 'p12':
        if cert.p12_bundle:
            response = HttpResponse(cert.p12_bundle, content_type='application/x-pkcs12')
            response['Content-Disposition'] = f'attachment; filename="{cert.common_name}.p12"'
        else:
            return HttpResponse('P12 bundle not available', status=404)
    else:
        return HttpResponse('Invalid file type', status=400)
    
    return response


@login_required
@require_POST
def client_cert_revoke(request, pk):
    """Revoke a Client Certificate."""
    cert = get_object_or_404(ClientCertificate, pk=pk)
    form = RevokeCertificateForm(request.POST)
    
    if form.is_valid():
        from django.utils import timezone
        cert.status = 'revoked'
        cert.revoked_at = timezone.now()
        cert.revocation_reason = form.cleaned_data['reason']
        cert.save()
        messages.success(request, f'Certificate "{cert.name}" went extinct! 🦴')
    
    return redirect('client_cert_detail', pk=pk)


@login_required
@require_POST
def client_cert_delete(request, pk):
    """Delete a Client Certificate."""
    cert = get_object_or_404(ClientCertificate, pk=pk)
    cert_name = cert.name
    cert.delete()
    messages.success(request, f'Client certificate "{cert_name}" has been deleted! 🦴')
    return redirect('client_cert_list')
