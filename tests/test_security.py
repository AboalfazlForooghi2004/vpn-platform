import pytest
from cryptography.fernet import Fernet

from vpn_platform.infrastructure.security.secrets import SecretBox, SecretDecryptionError


def test_secret_box_round_trip_and_wrong_key_failure() -> None:
    first = SecretBox(Fernet.generate_key().decode())
    second = SecretBox(Fernet.generate_key().decode())
    ciphertext = first.encrypt_text("client-private-key")

    assert b"client-private-key" not in ciphertext
    assert first.decrypt_text(ciphertext) == "client-private-key"
    with pytest.raises(SecretDecryptionError):
        second.decrypt_text(ciphertext)
