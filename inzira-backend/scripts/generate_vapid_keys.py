#!/usr/bin/env python3
"""Generate VAPID keys for Web Push. Paste output into .env."""

from base64 import urlsafe_b64encode

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01


def main() -> None:
    vapid = Vapid01()
    vapid.generate_keys()
    pub_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    priv_pem = vapid.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub_b64 = urlsafe_b64encode(pub_bytes).decode().rstrip("=")
    priv_one_line = priv_pem.strip().replace("\n", "\\n")
    print("Add these lines to inzira-backend/.env:\n")
    print(f"INZIRA_VAPID_PUBLIC_KEY={pub_b64}")
    print(f"INZIRA_VAPID_PRIVATE_KEY={priv_one_line}")
    print("INZIRA_VAPID_CLAIMS_EMAIL=mailto:alerts@inzira.rw")


if __name__ == "__main__":
    main()
