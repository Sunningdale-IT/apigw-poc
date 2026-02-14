# Generated migration for Certosaurus 🦖

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateAuthority',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('common_name', models.CharField(max_length=255)),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('organizational_unit', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(default='US', max_length=2)),
                ('state', models.CharField(blank=True, max_length=255)),
                ('locality', models.CharField(blank=True, max_length=255)),
                ('certificate_pem', models.TextField(blank=True)),
                ('private_key_pem', models.TextField(blank=True)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('is_root', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_cas', to=settings.AUTH_USER_MODEL)),
                ('parent_ca', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_cas', to='certificates.certificateauthority')),
            ],
            options={
                'verbose_name': 'Certificate Authority',
                'verbose_name_plural': 'Certificate Authorities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ServerCertificate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('common_name', models.CharField(help_text='Primary domain name (e.g., www.example.com)', max_length=255)),
                ('san_dns_names', models.TextField(blank=True, help_text='Comma-separated list of additional DNS names')),
                ('san_ip_addresses', models.TextField(blank=True, help_text='Comma-separated list of IP addresses')),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('organizational_unit', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(default='US', max_length=2)),
                ('state', models.CharField(blank=True, max_length=255)),
                ('locality', models.CharField(blank=True, max_length=255)),
                ('certificate_pem', models.TextField(blank=True)),
                ('private_key_pem', models.TextField(blank=True)),
                ('csr_pem', models.TextField(blank=True)),
                ('certificate_chain_pem', models.TextField(blank=True)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('key_size', models.IntegerField(choices=[(2048, '2048-bit'), (4096, '4096-bit')], default=2048)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('expired', 'Expired'), ('revoked', 'Revoked')], default='pending', max_length=20)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('revocation_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_server_certs', to=settings.AUTH_USER_MODEL)),
                ('issuing_ca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='server_certificates', to='certificates.certificateauthority')),
            ],
            options={
                'verbose_name': 'Server Certificate',
                'verbose_name_plural': 'Server Certificates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientCertificate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('common_name', models.CharField(help_text='Client identifier (e.g., user@example.com or service-name)', max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('organization', models.CharField(blank=True, max_length=255)),
                ('organizational_unit', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(default='US', max_length=2)),
                ('state', models.CharField(blank=True, max_length=255)),
                ('locality', models.CharField(blank=True, max_length=255)),
                ('certificate_pem', models.TextField(blank=True)),
                ('private_key_pem', models.TextField(blank=True)),
                ('csr_pem', models.TextField(blank=True)),
                ('p12_bundle', models.BinaryField(blank=True, null=True)),
                ('p12_password', models.CharField(blank=True, max_length=255)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('key_size', models.IntegerField(choices=[(2048, '2048-bit'), (4096, '4096-bit')], default=2048)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('expired', 'Expired'), ('revoked', 'Revoked')], default='pending', max_length=20)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('revocation_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_client_certs', to=settings.AUTH_USER_MODEL)),
                ('issuing_ca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_certificates', to='certificates.certificateauthority')),
            ],
            options={
                'verbose_name': 'Client Certificate',
                'verbose_name_plural': 'Client Certificates',
                'ordering': ['-created_at'],
            },
        ),
    ]
