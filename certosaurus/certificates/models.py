"""
Certificate models for Certosaurus. 🦖
A roaringly good certificate management system!
"""

import os
import uuid
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


class CertificateAuthority(models.Model):
    """Root or Intermediate Certificate Authority."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    common_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    organizational_unit = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='US')
    state = models.CharField(max_length=255, blank=True)
    locality = models.CharField(max_length=255, blank=True)
    
    # Certificate data (PEM encoded)
    certificate_pem = models.TextField(blank=True)
    private_key_pem = models.TextField(blank=True)  # Encrypted in production
    
    # Validity
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Hierarchy
    parent_ca = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='child_cas'
    )
    is_root = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_cas'
    )
    
    class Meta:
        verbose_name = 'Certificate Authority'
        verbose_name_plural = 'Certificate Authorities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({'Root' if self.is_root else 'Intermediate'})"
    
    @property
    def is_valid(self):
        """Check if the CA certificate is currently valid."""
        now = timezone.now()
        if self.valid_from and self.valid_until:
            # Make datetimes timezone-aware if they aren't
            valid_from = self.valid_from
            valid_until = self.valid_until
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            return valid_from <= now <= valid_until
        return False
    
    @property
    def days_until_expiry(self):
        """Get days until certificate expires."""
        if self.valid_until:
            now = timezone.now()
            valid_until = self.valid_until
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            delta = valid_until - now
            return max(0, delta.days)
        return 0


class ServerCertificate(models.Model):
    """SSL/TLS Server Certificate."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, help_text='Primary domain name (e.g., www.example.com)')
    
    # Subject Alternative Names (SANs)
    san_dns_names = models.TextField(blank=True, help_text='Comma-separated list of additional DNS names')
    san_ip_addresses = models.TextField(blank=True, help_text='Comma-separated list of IP addresses')
    
    # Organization details
    organization = models.CharField(max_length=255, blank=True)
    organizational_unit = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='US')
    state = models.CharField(max_length=255, blank=True)
    locality = models.CharField(max_length=255, blank=True)
    
    # Certificate data (PEM encoded)
    certificate_pem = models.TextField(blank=True)
    private_key_pem = models.TextField(blank=True)
    csr_pem = models.TextField(blank=True)
    certificate_chain_pem = models.TextField(blank=True)
    
    # Signing CA
    issuing_ca = models.ForeignKey(
        CertificateAuthority,
        on_delete=models.CASCADE,
        related_name='server_certificates'
    )
    
    # Validity
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    key_size = models.IntegerField(default=2048, choices=[(2048, '2048-bit'), (4096, '4096-bit')])
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_server_certs'
    )
    
    class Meta:
        verbose_name = 'Server Certificate'
        verbose_name_plural = 'Server Certificates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.common_name})"
    
    @property
    def is_valid(self):
        """Check if the certificate is currently valid."""
        if self.status != 'active':
            return False
        now = timezone.now()
        if self.valid_from and self.valid_until:
            valid_from = self.valid_from
            valid_until = self.valid_until
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            return valid_from <= now <= valid_until
        return False
    
    @property
    def days_until_expiry(self):
        """Get days until certificate expires."""
        if self.valid_until:
            now = timezone.now()
            valid_until = self.valid_until
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            delta = valid_until - now
            return max(0, delta.days)
        return 0
    
    def get_san_dns_list(self):
        """Get SANs as a list."""
        if self.san_dns_names:
            return [s.strip() for s in self.san_dns_names.split(',') if s.strip()]
        return []
    
    def get_san_ip_list(self):
        """Get IP SANs as a list."""
        if self.san_ip_addresses:
            return [s.strip() for s in self.san_ip_addresses.split(',') if s.strip()]
        return []


class ClientCertificate(models.Model):
    """Client Certificate for mTLS authentication."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, help_text='Client identifier (e.g., user@example.com or service-name)')
    email = models.EmailField(blank=True)
    
    # Organization details
    organization = models.CharField(max_length=255, blank=True)
    organizational_unit = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='US')
    state = models.CharField(max_length=255, blank=True)
    locality = models.CharField(max_length=255, blank=True)
    
    # Certificate data (PEM encoded)
    certificate_pem = models.TextField(blank=True)
    private_key_pem = models.TextField(blank=True)
    csr_pem = models.TextField(blank=True)
    
    # PKCS#12 bundle (for easy import into browsers/applications)
    p12_bundle = models.BinaryField(blank=True, null=True)
    p12_password = models.CharField(max_length=255, blank=True)  # Should be encrypted in production
    
    # Signing CA
    issuing_ca = models.ForeignKey(
        CertificateAuthority,
        on_delete=models.CASCADE,
        related_name='client_certificates'
    )
    
    # Validity
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    key_size = models.IntegerField(default=2048, choices=[(2048, '2048-bit'), (4096, '4096-bit')])
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_client_certs'
    )
    
    class Meta:
        verbose_name = 'Client Certificate'
        verbose_name_plural = 'Client Certificates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.common_name})"
    
    @property
    def is_valid(self):
        """Check if the certificate is currently valid."""
        if self.status != 'active':
            return False
        now = timezone.now()
        if self.valid_from and self.valid_until:
            valid_from = self.valid_from
            valid_until = self.valid_until
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            return valid_from <= now <= valid_until
        return False
    
    @property
    def days_until_expiry(self):
        """Get days until certificate expires."""
        if self.valid_until:
            now = timezone.now()
            valid_until = self.valid_until
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            delta = valid_until - now
            return max(0, delta.days)
        return 0
