import os
from cryptography.fernet import Fernet

def load_key():
    if os.path.exists("key.key"):
        with open("key.key", "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open("key.key", "wb") as key_file:
            key_file.write(key)
        return key

def save_token(token, key):
    f = Fernet(key)
    token_enc = f.encrypt(token.encode())
    with open("token.enc", "wb") as token_file:
        token_file.write(token_enc)

def load_token(key):
    if os.path.exists("token.enc"):
        with open("token.enc", "rb") as token_file:
            token_enc = token_file.read()
        try:
            f = Fernet(key)
            return f.decrypt(token_enc).decode()
        except Exception as e:
            print("Error decrypting token:", e)
            return None
    return None

def delete_token_files():
    for filename in ["token.enc", "key.key"]:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted {filename}")