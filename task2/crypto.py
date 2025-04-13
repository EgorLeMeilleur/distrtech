from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    return private_key, public_key

def generate_aes_key():
    return os.urandom(32)

def encrypt_with_rsa(public_key, data):
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext

def decrypt_with_rsa(private_key, ciphertext):
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext

def encrypt_with_aes(key, data):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + ciphertext

def decrypt_with_aes(key, data):
    iv = data[:16]
    ciphertext = data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

PRIVATE_KEY_FILE = 'private_key.pem'
PUBLIC_KEY_FILE = 'public_key.pem'

def load_or_generate_rsa_keys():
    if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
        with open(PRIVATE_KEY_FILE, "rb") as pk_file:
            private_key = serialization.load_pem_private_key(pk_file.read(), password=None)
        with open(PUBLIC_KEY_FILE, "rb") as pub_file:
            public_key = serialization.load_pem_public_key(pub_file.read())
        print("Загружены существующие RSA ключи")
    else:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        with open(PRIVATE_KEY_FILE, "wb") as pk_file:
            pk_file.write(pem_private)
        with open(PUBLIC_KEY_FILE, "wb") as pub_file:
            pub_file.write(pem_public)
        print("RSA ключи сгенерированы и сохранены.")
    return private_key, public_key