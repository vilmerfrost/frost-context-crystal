import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import settings


class EncryptionService:
    def __init__(self):
        self.fernet = self._create_fernet(settings.encryption_key)
    
    def _create_fernet(self, encryption_key: str) -> Fernet:
        """Create Fernet instance from encryption key"""
        # Derive a 32-byte key from the provided encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"context_crystal_salt",  # In production, use a random salt per key
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for storage"""
        encrypted_key = self.fernet.encrypt(api_key.encode())
        return encrypted_key.decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key for use"""
        decrypted_key = self.fernet.decrypt(encrypted_key.encode())
        return decrypted_key.decode()


# Global encryption service instance
encryption_service = EncryptionService()