from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

def generate_rsa_keys():
    """Генерация пары ключей RSA"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    return private_key, public_key

def save_rsa_keys(private_key, public_key, private_key_file, public_key_file):
    """Сохранение ключей RSA в файлы"""
    # Сохраняем приватный ключ
    with open(private_key_file, 'wb') as f:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        f.write(pem)
    
    # Сохраняем публичный ключ
    with open(public_key_file, 'wb') as f:
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        f.write(pem)

def load_rsa_public_key(public_key_file):
    """Загрузка публичного ключа RSA из файла"""
    with open(public_key_file, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key

def load_rsa_private_key(private_key_file):
    """Загрузка приватного ключа RSA из файла"""
    with open(private_key_file, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    return private_key

def generate_aes_key():
    """Генерация ключа AES"""
    return os.urandom(32)  # 256 бит

def encrypt_with_rsa(public_key, data):
    """Шифрование данных с помощью публичного ключа RSA"""
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
    """Дешифрование данных с помощью приватного ключа RSA"""
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
    """Шифрование данных с помощью ключа AES"""
    iv = os.urandom(16)  # Инициализационный вектор
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + ciphertext  # Возвращаем IV + зашифрованные данные

def decrypt_with_aes(key, data):
    """Дешифрование данных с помощью ключа AES"""
    iv = data[:16]  # Извлекаем IV
    ciphertext = data[16:]  # Извлекаем зашифрованные данные
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()