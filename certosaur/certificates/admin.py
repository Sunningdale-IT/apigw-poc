from django.contrib import admin
from .models import CertificateAuthority, ServerCertificate, ClientCertificate


@admin.register(CertificateAuthority)
class CertificateAuthorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'common_name', 'is_root', 'valid_from', 'valid_until', 'created_at']
    list_filter = ['is_root', 'created_at']
    search_fields = ['name', 'common_name', 'organization']
    readonly_fields = ['id', 'created_at', 'certificate_pem', 'valid_from', 'valid_until']


@admin.register(ServerCertificate)
class ServerCertificateAdmin(admin.ModelAdmin):
    list_display = ['name', 'common_name', 'status', 'issuing_ca', 'valid_until', 'created_at']
    list_filter = ['status', 'issuing_ca', 'created_at']
    search_fields = ['name', 'common_name', 'organization']
    readonly_fields = ['id', 'created_at', 'certificate_pem', 'valid_from', 'valid_until']


@admin.register(ClientCertificate)
class ClientCertificateAdmin(admin.ModelAdmin):
    list_display = ['name', 'common_name', 'status', 'issuing_ca', 'valid_until', 'created_at']
    list_filter = ['status', 'issuing_ca', 'created_at']
    search_fields = ['name', 'common_name', 'email', 'organization']
    readonly_fields = ['id', 'created_at', 'certificate_pem', 'valid_from', 'valid_until']
