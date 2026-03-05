"""
Django management command to populate initial Certificate Authorities.
Creates a root CA (alpha) and two intermediate CAs (commercial, government).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from certificates.models import CertificateAuthority
from certificates.cert_utils import generate_ca_certificate, serialize_certificate, serialize_private_key
from datetime import datetime


class Command(BaseCommand):
    help = 'Populate initial Certificate Authorities (alpha root CA, commercial and government sub CAs)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force population even if CAs already exist'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Check if CAs already exist
        existing_count = CertificateAuthority.objects.count()
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Database already contains {existing_count} CA(s). '
                    f'Use --force to populate anyway.'
                )
            )
            return
        
        with transaction.atomic():
            # Create root CA: alpha
            self.stdout.write('Creating root CA: alpha...')
            alpha_cert, alpha_key = generate_ca_certificate(
                common_name='Alpha Root CA',
                organization='Alpha Corporation',
                organizational_unit='PKI Division',
                country='US',
                state='California',
                locality='San Francisco',
                validity_days=7300,  # 20 years
                key_size=4096,
            )
            
            alpha_ca = CertificateAuthority.objects.create(
                name='alpha',
                common_name='Alpha Root CA',
                organization='Alpha Corporation',
                organizational_unit='PKI Division',
                country='US',
                state='California',
                locality='San Francisco',
                certificate_pem=serialize_certificate(alpha_cert).decode('utf-8'),
                private_key_pem=serialize_private_key(alpha_key).decode('utf-8'),
                valid_from=alpha_cert.not_valid_before,
                valid_until=alpha_cert.not_valid_after,
                is_root=True,
                parent_ca=None,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created root CA: {alpha_ca.name}'))
            
            # Create intermediate CA: commercial
            self.stdout.write('Creating intermediate CA: commercial...')
            commercial_cert, commercial_key = generate_ca_certificate(
                common_name='Commercial Intermediate CA',
                organization='Alpha Corporation',
                organizational_unit='Commercial Division',
                country='US',
                state='California',
                locality='San Francisco',
                validity_days=3650,  # 10 years
                key_size=4096,
                parent_cert=alpha_cert,
                parent_key=alpha_key,
            )
            
            commercial_ca = CertificateAuthority.objects.create(
                name='commercial',
                common_name='Commercial Intermediate CA',
                organization='Alpha Corporation',
                organizational_unit='Commercial Division',
                country='US',
                state='California',
                locality='San Francisco',
                certificate_pem=serialize_certificate(commercial_cert).decode('utf-8'),
                private_key_pem=serialize_private_key(commercial_key).decode('utf-8'),
                valid_from=commercial_cert.not_valid_before,
                valid_until=commercial_cert.not_valid_after,
                is_root=False,
                parent_ca=alpha_ca,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created intermediate CA: {commercial_ca.name}'))
            
            # Create intermediate CA: government
            self.stdout.write('Creating intermediate CA: government...')
            government_cert, government_key = generate_ca_certificate(
                common_name='Government Intermediate CA',
                organization='Alpha Corporation',
                organizational_unit='Government Division',
                country='US',
                state='California',
                locality='San Francisco',
                validity_days=3650,  # 10 years
                key_size=4096,
                parent_cert=alpha_cert,
                parent_key=alpha_key,
            )
            
            government_ca = CertificateAuthority.objects.create(
                name='government',
                common_name='Government Intermediate CA',
                organization='Alpha Corporation',
                organizational_unit='Government Division',
                country='US',
                state='California',
                locality='San Francisco',
                certificate_pem=serialize_certificate(government_cert).decode('utf-8'),
                private_key_pem=serialize_private_key(government_key).decode('utf-8'),
                valid_from=government_cert.not_valid_before,
                valid_until=government_cert.not_valid_after,
                is_root=False,
                parent_ca=alpha_ca,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created intermediate CA: {government_ca.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🦖 Certosaur initialized successfully!'
                f'\nCreated 1 root CA (alpha) and 2 intermediate CAs (commercial, government)'
            )
        )
