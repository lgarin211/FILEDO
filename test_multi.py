import io
import os
# Set env to avoid app.run? imported app doesn't run if guarded.
from app import app, get_db_connection

def test_multi_upload():
    client = app.test_client()
    
    # Create dummy files
    file1 = (io.BytesIO(b"content of file 1"), 'file1.txt')
    file2 = (io.BytesIO(b"content of file 2"), 'file2.txt')
    
    data = {
        'nomor_surat': 'MULTI-TEST/001',
        'file': [file1, file2]
    }
    
    print("Uploading...")
    rv = client.post('/upload', data=data, content_type='multipart/form-data')
    print(f"Upload Status: {rv.status_code}")
    print(f"Upload Response: {rv.json}")
    
    if rv.status_code != 200:
        print("Upload failed!")
        return

    # Check DB for the key
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT encrip FROM surat WHERE no_surat = 'MULTI-TEST/001' ORDER BY id DESC LIMIT 1")
    res = cur.fetchone()
    conn.close()
    
    if not res:
        print("Key not found in DB!")
        return
        
    key = res[0]
    print(f"Retrieved Key from DB (truncated): {key[:50]}...")
    
    # Now call /retrieve
    print("Calling /retrieve...")
    rv_ret = client.get(f'/retrieve?key={key}')
    print(f"Retrieve Status: {rv_ret.status_code}")
    print(f"Retrieve Response: {rv_ret.json}")
    
    # clean up?
    # os.remove... well, files are random. logic is complex to cleanup without path.
    # response has stored_path.
    stored_path = rv.json['stored_path']
    # Dangerous to delete whole folder if it's shared.
    # "d:\\EXPERIMENT\\FILEDO\\files\\surat"
    # I'll leave them.

if __name__ == '__main__':
    test_multi_upload()
