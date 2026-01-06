import unittest
import os
import shutil
import tempfile
from cryptography.fernet import Fernet
# Import functions to test
from utils import decrypt_filename, find_file, process_file_retrieval
from app import app

class TestFileRetrieval(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock search directories
        self.dir1 = os.path.join(self.test_dir, 'files', 'surat')
        self.dir2 = os.path.join(self.test_dir, 'files2', 'surat')
        os.makedirs(self.dir1)
        os.makedirs(self.dir2)
        
        # Create a staging directory
        self.staging_dir = os.path.join(self.test_dir, 'home', 'scpkan')
        
        # Create a dummy file in dir2 (simulating it's not in the first path)
        self.filename = "secret_report.pdf"
        self.file_path = os.path.join(self.dir2, self.filename)
        with open(self.file_path, 'w') as f:
            f.write("This is a secret report content.")
            
        # Setup Encryption
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.encrypted_name = self.fernet.encrypt(self.filename.encode())
        
        # Configure App for testing
        app.config['SECRET_KEY'] = self.key
        app.config['SEARCH_PATHS'] = [self.dir1, self.dir2] # Use our temp dirs
        app.config['STAGING_DIR'] = self.staging_dir
        
        self.app = app.test_client()

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    def test_decryption(self):
        # Test if decryption works
        decrypted = decrypt_filename(self.encrypted_name, self.key)
        self.assertEqual(decrypted, self.filename)

    def test_find_file(self):
        # Test finding the file
        paths = [self.dir1, self.dir2]
        found_path = find_file(self.filename, paths)
        self.assertIsNotNone(found_path)
        self.assertEqual(found_path, self.file_path)
        
    def test_find_file_not_exist(self):
        # Test finding a non-existent file
        found_path = find_file("nope.txt", [self.dir1, self.dir2])
        self.assertIsNone(found_path)

    def test_process_file(self):
        # Test zipping logic
        zip_name = process_file_retrieval(self.file_path, self.staging_dir)
        self.assertIsNotNone(zip_name)
        self.assertTrue(zip_name.endswith('.zip'))
        self.assertTrue(os.path.exists(os.path.join(self.staging_dir, zip_name)))

    def test_endpoint(self):
        # Test the full endpoint flow
        response = self.app.get(f'/retrieve?key={self.encrypted_name.decode()}')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['original_filename'], self.filename)
        self.assertIn("scp user@", json_data['download_command'])
        self.assertIn(".zip", json_data['download_command'])

if __name__ == '__main__':
    unittest.main()
