"""Create the local HTTPS certificate used by Nginx."""

import argparse
from datetime import datetime, timedelta, timezone
import ipaddress
import os
from pathlib import Path
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def make_certificate(output):
    output.mkdir(parents=True, exist_ok=True)
    key_file = output / "notesapp.key"
    certificate_file = output / "notesapp.crt"
    if key_file.exists() or certificate_file.exists():
        if key_file.is_file() and certificate_file.is_file():
            print("Certificate and key already exist; kept both files unchanged.")
            return
        raise ValueError(
            "Both notesapp.key and notesapp.crt are needed. "
            "Only part of the certificate pair exists; no files were changed."
        )

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                x509.IPAddress(ipaddress.ip_address("::1")),
            ]),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    private_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Create the private key with owner-only permissions where supported.
    key_descriptor = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(key_descriptor, "wb") as destination:
        destination.write(private_bytes)
    with certificate_file.open("xb") as destination:
        destination.write(certificate.public_bytes(serialization.Encoding.PEM))
    print(f"Created notesapp.key and notesapp.crt in {output}.")


def main():
    parser = argparse.ArgumentParser(description="Create a self-signed localhost HTTPS certificate.")
    parser.add_argument("--output", type=Path, default=Path("/host/nginx/certs"))
    args = parser.parse_args()
    try:
        make_certificate(args.output)
    except (OSError, ValueError) as error:
        print(f"Certificate error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
