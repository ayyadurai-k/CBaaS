import base64
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken

class Encryptor:
    @staticmethod
    def _fernet() -> Fernet:
        key = settings.ENCRYPTION_SECRET_KEY
        if not key:
            raise RuntimeError("ENCRYPTION_SECRET_KEY not configured")
        try:
            return Fernet(key)
        except Exception:
            return Fernet(base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b"0")))

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if plaintext is None:
            return ""
        return cls._fernet().encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return cls._fernet().decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            return ""