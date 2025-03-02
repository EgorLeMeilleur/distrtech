import os
from cryptography.fernet import Fernet

TOKEN_DIR = "tokens"

def ensure_token_dir():
    if not os.path.exists(TOKEN_DIR):
        os.makedirs(TOKEN_DIR)

def get_filenames(token_type):
    key_filename = os.path.join(TOKEN_DIR, f"{token_type}.key")
    token_filename = os.path.join(TOKEN_DIR, f"{token_type}.enc")
    return key_filename, token_filename

def load_key(token_type):
    ensure_token_dir()
    key_filename, _ = get_filenames(token_type)
    if os.path.exists(key_filename):
        with open(key_filename, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(key_filename, "wb") as key_file:
            key_file.write(key)
        return key

def save_token(token, key, token_type):
    ensure_token_dir()
    _, token_filename = get_filenames(token_type)
    f = Fernet(key)
    token_enc = f.encrypt(token.encode())
    with open(token_filename, "wb") as token_file:
        token_file.write(token_enc)

def load_token(key, token_type):
    _, token_filename = get_filenames(token_type)
    if os.path.exists(token_filename):
        with open(token_filename, "rb") as token_file:
            token_enc = token_file.read()
        try:
            f = Fernet(key)
            return f.decrypt(token_enc).decode()
        except Exception as e:
            print("Error decrypting token:", e)
            return None
    return None

def delete_token_files():
    for token_type in ['oauth2', 'pat']:
        key_filename, token_filename = get_filenames(token_type)
        for filename in [key_filename, token_filename]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"Deleted {filename}")
