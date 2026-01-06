import os

class Config:
    # Secret key for encryption/decryption. 
    # IN PRODUCTION: Retrieve this from environment variables!
    # generate one via: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    SECRET_KEY = os.environ.get('SECRET_KEY', 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')
    
    # Locations where the files might be stored
    SEARCH_PATHS = [
        '/files/surat/',
        '/files2/surat/',
        '/files3/surat/',
        # For local testing on Windows, you might add:
        # 'C:\\Users\\lagus\\files\\surat\\'
    ]
    
    # Destination directory where files will be zipped
    STAGING_DIR = '/home/scpkan'
    # For local testing on Windows:
    # STAGING_DIR = 'd:\\EXPERIMENT\\FILEDO\\staging'

    # Database Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'lfdeo'
