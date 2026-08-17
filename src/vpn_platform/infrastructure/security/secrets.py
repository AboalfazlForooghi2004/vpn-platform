from cryptography.fernet import Fernet, InvalidToken


class SecretDecryptionError(RuntimeError):
    pass


class SecretBox:
    """Small envelope boundary; production should load its key from a secret store."""

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt_text(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode())

    def decrypt_text(self, ciphertext: bytes) -> str:
        try:
            return self._fernet.decrypt(ciphertext).decode()
        except InvalidToken as exc:
            raise SecretDecryptionError("secret cannot be decrypted") from exc
