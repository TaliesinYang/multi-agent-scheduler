"""
Security Module - API Key Encryption and Management

Provides secure storage and retrieval of API keys using encryption.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pathlib import Path


class SecureKeyManager:
    """
    Secure API key manager with encryption

    Features:
    - AES encryption for API keys
    - Key derivation from master password
    - Secure file storage
    - In-memory caching

    Example:
        >>> manager = SecureKeyManager()
        >>> manager.set_key('ANTHROPIC_API_KEY', 'sk-ant-...')
        >>> key = manager.get_key('ANTHROPIC_API_KEY')
        >>> print(key)
        sk-ant-...
    """

    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize secure key manager

        Args:
            master_password: Master password for encryption.
                           If None, uses environment variable MASTER_PASSWORD
                           or generates a new one.
        """
        self.key_file = Path.home() / '.mas_keys.enc'
        self.master_password = master_password or os.getenv('MASTER_PASSWORD')

        if not self.master_password:
            # Generate a new master password
            self.master_password = base64.urlsafe_b64encode(os.urandom(32)).decode()
            print(f"⚠️  Generated new master password. Save it securely:")
            print(f"   export MASTER_PASSWORD='{self.master_password}'")

        self.cipher = self._init_cipher()
        self.keys_cache: dict[str, str] = {}

    def _init_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with key derived from master password

        Returns:
            Fernet cipher instance
        """
        # Derive encryption key from master password using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'multi-agent-scheduler-salt',  # Static salt for reproducibility
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_password.encode())
        )
        return Fernet(key)

    def set_key(self, name: str, value: str) -> None:
        """
        Store API key with encryption

        Args:
            name: Key name (e.g., 'ANTHROPIC_API_KEY')
            value: API key value

        Example:
            >>> manager.set_key('ANTHROPIC_API_KEY', 'sk-ant-...')
        """
        # Update cache
        self.keys_cache[name] = value

        # Save to encrypted file
        self._save_to_file()

    def get_key(self, name: str) -> Optional[str]:
        """
        Retrieve API key (from cache or environment or file)

        Args:
            name: Key name

        Returns:
            API key value or None if not found

        Priority:
            1. Cache
            2. Environment variable
            3. Encrypted file
        """
        # 1. Check cache
        if name in self.keys_cache:
            return self.keys_cache[name]

        # 2. Check environment variable
        env_value = os.getenv(name)
        if env_value:
            self.keys_cache[name] = env_value
            return env_value

        # 3. Load from encrypted file
        self._load_from_file()

        return self.keys_cache.get(name)

    def delete_key(self, name: str) -> None:
        """
        Delete API key

        Args:
            name: Key name
        """
        if name in self.keys_cache:
            del self.keys_cache[name]

        self._save_to_file()

    def list_keys(self) -> list[str]:
        """
        List all stored key names

        Returns:
            List of key names
        """
        self._load_from_file()
        return list(self.keys_cache.keys())

    def _save_to_file(self) -> None:
        """Save encrypted keys to file"""
        try:
            # Serialize keys
            import json
            data = json.dumps(self.keys_cache)

            # Encrypt
            encrypted = self.cipher.encrypt(data.encode())

            # Save to file
            self.key_file.write_bytes(encrypted)

        except Exception as e:
            print(f"⚠️  Warning: Failed to save keys: {e}")

    def _load_from_file(self) -> None:
        """Load encrypted keys from file"""
        if not self.key_file.exists():
            return

        try:
            # Read encrypted data
            encrypted = self.key_file.read_bytes()

            # Decrypt
            decrypted = self.cipher.decrypt(encrypted)

            # Deserialize
            import json
            self.keys_cache.update(json.loads(decrypted))

        except Exception as e:
            print(f"⚠️  Warning: Failed to load keys: {e}")


# Global instance
_global_key_manager: Optional[SecureKeyManager] = None


def get_key_manager() -> SecureKeyManager:
    """
    Get global SecureKeyManager instance

    Returns:
        Global SecureKeyManager instance
    """
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = SecureKeyManager()
    return _global_key_manager


def get_secure_api_key(name: str) -> Optional[str]:
    """
    Convenience function to get API key

    Args:
        name: Key name

    Returns:
        API key value or None

    Example:
        >>> api_key = get_secure_api_key('ANTHROPIC_API_KEY')
    """
    return get_key_manager().get_key(name)


# Example usage
if __name__ == "__main__":
    # Test the secure key manager
    manager = SecureKeyManager()

    # Store a test key
    manager.set_key('TEST_API_KEY', 'test-value-123')

    # Retrieve the key
    retrieved = manager.get_key('TEST_API_KEY')
    print(f"Retrieved key: {retrieved}")

    # List all keys
    print(f"All keys: {manager.list_keys()}")

    # Delete the key
    manager.delete_key('TEST_API_KEY')
    print(f"After delete: {manager.list_keys()}")
