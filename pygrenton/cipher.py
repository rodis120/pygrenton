from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from base64 import b64decode

class GrentonCypher:

    def __init__(self, key: str, iv: str) -> None:
        self._key = b64decode(key)
        self._iv = b64decode(iv)
        self._padder = padding.PKCS7(128).padder()
        self._unpadder = padding.PKCS7(128).unpadder()
        self._cypher = Cipher(algorithms.AES(self._key), modes.CBC(self._iv), backend=default_backend())
        self._encryptor = self._cypher.encryptor()
        self._decryptor = self._cypher.decryptor()

    def encrypt(self, data: bytes) -> bytes:
        data = self._padder.update(data) + self._padder.finalize()
        return self._encryptor.update(data) + self._encryptor.finalize()

    def decrypt(self, data: bytes) -> bytes:
        data = self._decryptor.update(data) + self._decryptor.finalize()
        return self._unpadder.update(data) + self._unpadder.finalize()
