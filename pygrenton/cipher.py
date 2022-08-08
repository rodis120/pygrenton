from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from base64 import b64decode

class GrentonCypher:

    def __init__(self, key: str, iv: str) -> None:
        self._key = b64decode(key)
        self._iv = b64decode(iv)
        self._padding = padding.PKCS7(128)
        self._cypher = Cipher(
            algorithms.AES(self._key), modes.CBC(self._iv), backend=default_backend()
        )

    def encrypt(self, data: bytes) -> bytes:
        encryptor = self._cypher.encryptor()
        padder = self._padding.padder()
        data = padder.update(data) + padder.finalize()
        return encryptor.update(data) + encryptor.finalize()

    def decrypt(self, data: bytes) -> bytes:
        decryptor = self._cypher.decryptor()
        unpadder = self._padding.unpadder()
        data = decryptor.update(data) + decryptor.finalize()
        return unpadder.update(data) + unpadder.finalize()
