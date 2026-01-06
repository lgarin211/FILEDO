import os
import shutil
import uuid
import zipfile
import random
import json
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from config import Config

def decrypt_data(encrypted_key: str, secret_key: str):
    """
    Decrypts the encrypted data (expects a JSON list of filenames).
    Returns a Python list of filenames.
    """
    try:
        f = Fernet(secret_key.strip())
        # Verify if it's bytes or string, Fernet expects bytes
        if isinstance(encrypted_key, str):
            encrypted_key = encrypted_key.encode()
        
        decrypted_bytes = f.decrypt(encrypted_key)
        decrypted_str = decrypted_bytes.decode()
        
        # Try to load as JSON (list of files)
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            # Fallback for legacy single strings (if any exist)
            return [decrypted_str]
            
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def find_files_in_paths(filenames: list, search_paths: list) -> list:
    """
    Searches for files. 
    NOTE: If we trust the DB path, we might not use this iteratively. 
    But this helper can find files if we only have filenames.
    Returns list of found full paths.
    """
    found_paths = []
    for filename in filenames:
        for path in search_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                found_paths.append(full_path)
                break
    return found_paths

def process_file_retrieval(source_file_paths: list, staging_dir: str) -> str:
    """
    Zips multiple files into one archive.
    source_file_paths: List of absolute paths to files.
    Returns the name of the zip file.
    """
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir)

    # Generate a unique name for the zip
    unique_id = str(uuid.uuid4())
    zip_filename = f"secure_files_{unique_id}.zip"
    zip_file_path = os.path.join(staging_dir, zip_filename)

    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_file_paths:
                if os.path.exists(file_path):
                    # Keep original filename in zip
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname=arcname)
        
        return zip_filename
    except Exception as e:
        print(f"Error zipping files: {e}")
        return None

def save_file_to_dir(file_storage, target_dir: str) -> str:
    """
    Saves a single file to the specific directory.
    Returns the full path.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    filename = secure_filename(file_storage.filename)
    full_path = os.path.join(target_dir, filename)
    file_storage.save(full_path)
    return full_path

def encrypt_data(data, secret_key: str) -> str:
    """
    Encrypts data (list or string).
    If list, converts to JSON string first.
    Returns encrypted string.
    """
    try:
        f = Fernet(secret_key.strip())
        
        # Serialize if list
        if isinstance(data, list):
            text_to_encrypt = json.dumps(data)
        else:
            text_to_encrypt = str(data)
            
        encrypted = f.encrypt(text_to_encrypt.encode()).decode()
        return encrypted
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

