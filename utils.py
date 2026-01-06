import os
import shutil
import uuid
import zipfile
import random
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from config import Config

def decrypt_filename(encrypted_key: str, secret_key: str) -> str:
    """
    Decrypts the encrypted filename using the provided secret key.
    """
    try:
        f = Fernet(secret_key.strip())
        # Verify if it's bytes or string, Fernet expects bytes
        if isinstance(encrypted_key, str):
            encrypted_key = encrypted_key.encode()
        
        decrypted_name = f.decrypt(encrypted_key).decode()
        return decrypted_name
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def find_file(filename: str, search_paths: list) -> str:
    """
    Searches for a file in the provided list of directories.
    Returns the full path if found, else None.
    """
    for path in search_paths:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            return full_path
    return None

def process_file_retrieval(source_file_path: str, staging_dir: str) -> str:
    """
    Copies the file to the staging directory and zips it with a unique name.
    Returns the path to the zip file.
    """
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir)

    # Generate a unique name for the zip
    unique_id = str(uuid.uuid4())
    zip_filename = f"secure_file_{unique_id}.zip"
    zip_file_path = os.path.join(staging_dir, zip_filename)

    # Use zipfile to compress the file
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Arcname is the name of the file inside the zip. 
            # We keep the original filename.
            original_filename = os.path.basename(source_file_path)
            zipf.write(source_file_path, arcname=original_filename)
        
        return zip_filename
    except Exception as e:
        print(f"Error zipping file: {e}")
        return None

def save_file_randomly(file_storage, search_paths: list) -> str:
    """
    Saves the uploaded file to a random directory from search_paths.
    Returns the full path where it was saved.
    """
    if not search_paths:
        return None
        
    target_dir = random.choice(search_paths)
    
    # Ensure directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    filename = secure_filename(file_storage.filename)
    full_path = os.path.join(target_dir, filename)
    
    file_storage.save(full_path)
    return full_path

def encrypt_filename(filename: str, secret_key: str) -> str:
    """
    Encrypts the filename using the provided secret key.
    Returns the encrypted string.
    """
    try:
        f = Fernet(secret_key.strip())
        encrypted = f.encrypt(filename.encode()).decode()
        return encrypted
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

