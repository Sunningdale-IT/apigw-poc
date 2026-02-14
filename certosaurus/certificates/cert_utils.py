"""
Certificate generation utilities using cryptography library.
Certosaurus - Prehistoric-powered certificate generation! 🦕
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from ipaddress import ip_address


def generate_private_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """Generate an RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


def serialize_private_key(private_key: rsa.RSAPrivateKey, password: Optional[str] = None) -> bytes:
    """Serialize private key to PEM format."""
    encryption = serialization.NoEncryption()
    if password:
        encryption = serialization.BestAvailableEncryption(password.encode())
    
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=encryption,
    )


def serialize_certificate(certificate: x509.Certificate) -> bytes:
    """Serialize certificate to PEM format."""
    return certificate.public_bytes(serialization.Encoding.PEM)


def build_subject_name(
    common_name: str,
    organization: str = '',
    organizational_unit: str = '',
    country: str = 'US',
    state: str = '',
    locality: str = '',
    email: str = '',
) -> x509.Name:
    """Build an X.509 subject name."""
    attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    
    if organization:
        attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
    if organizational_unit:
        attributes.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit))
    if country:
        attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
    if state:
        attributes.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state))
    if locality:
        attributes.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
    if email:
        attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
    
    return x509.Name(attributes)


def generate_ca_certificate(
    common_name: str,
    organization: str = '',
    organizational_unit: str = '',
    country: str = 'US',
    state: str = '',
    locality: str = '',
    validity_days: int = 3650,
    key_size: int = 4096,
    parent_cert: Optional[x509.Certificate] = None,
    parent_key: Optional[rsa.RSAPrivateKey] = None,
) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
    """
    Generate a Certificate Authority certificate.
    
    If parent_cert and parent_key are provided, creates an intermediate CA.
    Otherwise, creates a self-signed root CA.
    """
    private_key = generate_private_key(key_size)
    public_key = private_key.public_key()
    
    subject = build_subject_name(
        common_name=common_name,
        organization=organization,
        organizational_unit=organizational_unit,
        country=country,
        state=state,
        locality=locality,
    )
    
    now = datetime.utcnow()
    
    # If no parent, this is a root CA (self-signed)
    if parent_cert is None or parent_key is None:
        issuer = subject
        signing_key = private_key
        path_length = 1  # Can sign intermediate CAs
    else:
        issuer = parent_cert.subject
        signing_key = parent_key
        path_length = 0  # Intermediate CA, cannot sign other CAs
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(now)
    builder = builder.not_valid_after(now + timedelta(days=validity_days))
    
    # CA extensions
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=path_length),
        critical=True,
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    
    if parent_cert is not None:
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(parent_cert.public_key()),
            critical=False,
        )
    
    certificate = builder.sign(signing_key, hashes.SHA256())
    
    return certificate, private_key


def generate_server_certificate(
    common_name: str,
    ca_cert: x509.Certificate,
    ca_key: rsa.RSAPrivateKey,
    san_dns_names: List[str] = None,
    san_ip_addresses: List[str] = None,
    organization: str = '',
    organizational_unit: str = '',
    country: str = 'US',
    state: str = '',
    locality: str = '',
    validity_days: int = 365,
    key_size: int = 2048,
) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
    """Generate a server/SSL certificate signed by the CA."""
    private_key = generate_private_key(key_size)
    public_key = private_key.public_key()
    
    subject = build_subject_name(
        common_name=common_name,
        organization=organization,
        organizational_unit=organizational_unit,
        country=country,
        state=state,
        locality=locality,
    )
    
    now = datetime.utcnow()
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(now)
    builder = builder.not_valid_after(now + timedelta(days=validity_days))
    
    # Server certificate extensions
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    builder = builder.add_extension(
        x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
        critical=False,
    )
    
    # Subject Alternative Names
    san_entries = [x509.DNSName(common_name)]
    
    if san_dns_names:
        for dns_name in san_dns_names:
            if dns_name and dns_name != common_name:
                san_entries.append(x509.DNSName(dns_name))
    
    if san_ip_addresses:
        for ip_str in san_ip_addresses:
            if ip_str:
                san_entries.append(x509.IPAddress(ip_address(ip_str)))
    
    builder = builder.add_extension(
        x509.SubjectAlternativeName(san_entries),
        critical=False,
    )
    
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()),
        critical=False,
    )
    
    certificate = builder.sign(ca_key, hashes.SHA256())
    
    return certificate, private_key


def generate_client_certificate(
    common_name: str,
    ca_cert: x509.Certificate,
    ca_key: rsa.RSAPrivateKey,
    email: str = '',
    organization: str = '',
    organizational_unit: str = '',
    country: str = 'US',
    state: str = '',
    locality: str = '',
    validity_days: int = 365,
    key_size: int = 2048,
) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
    """Generate a client certificate for mTLS authentication."""
    private_key = generate_private_key(key_size)
    public_key = private_key.public_key()
    
    subject = build_subject_name(
        common_name=common_name,
        organization=organization,
        organizational_unit=organizational_unit,
        country=country,
        state=state,
        locality=locality,
        email=email,
    )
    
    now = datetime.utcnow()
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(now)
    builder = builder.not_valid_after(now + timedelta(days=validity_days))
    
    # Client certificate extensions
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    builder = builder.add_extension(
        x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
        critical=False,
    )
    
    # Add email to SAN if provided
    if email:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.RFC822Name(email)]),
            critical=False,
        )
    
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(public_key),
        critical=False,
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()),
        critical=False,
    )
    
    certificate = builder.sign(ca_key, hashes.SHA256())
    
    return certificate, private_key


def create_p12_bundle(
    certificate: x509.Certificate,
    private_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    password: str,
    friendly_name: str = 'client-cert',
) -> bytes:
    """Create a PKCS#12 bundle containing the certificate and private key."""
    return pkcs12.serialize_key_and_certificates(
        name=friendly_name.encode(),
        key=private_key,
        cert=certificate,
        cas=[ca_cert],
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode()),
    )


def generate_random_password(length: int = 16) -> str:
    """Generate a random password for P12 bundles."""
    return secrets.token_urlsafe(length)


def load_certificate_from_pem(pem_data: str) -> x509.Certificate:
    """Load a certificate from PEM format."""
    return x509.load_pem_x509_certificate(pem_data.encode())


def load_private_key_from_pem(pem_data: str, password: Optional[str] = None) -> rsa.RSAPrivateKey:
    """Load a private key from PEM format."""
    pwd = password.encode() if password else None
    return serialization.load_pem_private_key(pem_data.encode(), password=pwd)


def get_certificate_info(cert: x509.Certificate) -> dict:
    """Extract information from a certificate."""
    subject = cert.subject
    
    def get_attr(oid):
        try:
            return subject.get_attributes_for_oid(oid)[0].value
        except (IndexError, KeyError):
            return ''
    
    return {
        'common_name': get_attr(NameOID.COMMON_NAME),
        'organization': get_attr(NameOID.ORGANIZATION_NAME),
        'organizational_unit': get_attr(NameOID.ORGANIZATIONAL_UNIT_NAME),
        'country': get_attr(NameOID.COUNTRY_NAME),
        'state': get_attr(NameOID.STATE_OR_PROVINCE_NAME),
        'locality': get_attr(NameOID.LOCALITY_NAME),
        'serial_number': cert.serial_number,
        'valid_from': cert.not_valid_before_utc,
        'valid_until': cert.not_valid_after_utc,
    }
