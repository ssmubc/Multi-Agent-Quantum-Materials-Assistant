#!/usr/bin/env python3
"""Create self-signed certificate for ALB"""

import boto3
import base64
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

def create_self_signed_cert():
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "WA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Seattle"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QuantumMatter"),
        x509.NameAttribute(NameOID.COMMON_NAME, "quantum-matter-app"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).sign(private_key, hashes.SHA256())
    
    # Serialize to PEM
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    return cert_pem, key_pem

def upload_to_iam(cert_pem, key_pem):
    iam = boto3.client('iam')
    
    response = iam.upload_server_certificate(
        ServerCertificateName='quantum-matter-self-signed',
        CertificateBody=cert_pem,
        PrivateKey=key_pem
    )
    
    return response['ServerCertificateMetadata']['Arn']

if __name__ == "__main__":
    print("Creating self-signed certificate...")
    cert_pem, key_pem = create_self_signed_cert()
    
    print("Uploading to IAM...")
    cert_arn = upload_to_iam(cert_pem, key_pem)
    
    print(f"Certificate ARN: {cert_arn}")
    print("Use this ARN in your ALB HTTPS listener configuration.")