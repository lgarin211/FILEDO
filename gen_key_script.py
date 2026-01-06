from cryptography.fernet import Fernet
import sys

def main():
    # 1. Generate a Key (or use an existing one if provided)
    key = Fernet.generate_key()
    print(f"Generated SECRET_KEY: {key.decode()}")
    
    fernet = Fernet(key)
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_document.pdf"
        
    # 2. Encrypt the filename
    encrypted_filename = fernet.encrypt(filename.encode()).decode()
    print(f"\nOriginal Filename: {filename}")
    print(f"Encrypted Key (for URL): {encrypted_filename}")
    
    print("\n--- Usage Instructions ---")
    print("1. Copy the SECRET_KEY to your config.py or environment variable.")
    print(f"2. Use the Encrypted Key in your URL: http://localhost:5000/retrieve?key={encrypted_filename}")

if __name__ == "__main__":
    main()
