from flask import Flask, request, jsonify, render_template
from config import Config
from utils import decrypt_filename, find_file, process_file_retrieval, save_file_randomly, encrypt_filename
import os
import mysql.connector

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_file():
    """
    Endpoint to search for a file via the web UI using 'nomor_surat'.
    Input JSON: { "data": "SK/..." } (Using generic key or specific 'nomor_surat')
    """
    data = request.get_json()
    # Accept 'nomor_surat' or 'filename' to be flexible, but UI sends 'nomor_surat' via the input name but let's check
    # The UI input name is 'nomor_surat', but the JS sends { filename: ... }. 
    # Let's support both logic: direct filename OR lookup by no_surat.
    # Given the user request "masukin nomor surat -> dapat file", we should look up DB first.
    
    query_input = data.get('filename') # The JS sends 'filename' key currently.
    
    if not query_input:
        return jsonify({"error": "Nomor Surat is required"}), 400
        
    filename_to_search = query_input
    
    # 1. Database Lookup
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # exact match or like? User said "memasaukan nomor suratnya saja". Let's try exact first.
        cursor.execute("SELECT path FROM surat WHERE no_surat = %s LIMIT 1", (query_input,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            db_path = result[0]
            # Extract basic filename from the DB path (e.g. /files/surat/doc.pdf -> doc.pdf)
            filename_to_search = os.path.basename(db_path)
        else:
            # Fallback: maybe they entered the filename directly?
            # We keep filename_to_search as query_input
            pass
            
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database connection failed"}), 500

    # 2. Find the file (System Search)
    search_paths = app.config['SEARCH_PATHS']
    found_path = find_file(filename_to_search, search_paths)
    
    if not found_path:
        return jsonify({"error": f"File '{filename_to_search}' not found in storage"}), 404

    # 3. Process (zip/move)
    staging_dir = app.config['STAGING_DIR']
    zip_filename = process_file_retrieval(found_path, staging_dir)
    
    if not zip_filename:
        return jsonify({"error": "System error: Failed to process file"}), 500

    # 4. Generate SCP Command
    server_host = request.host.split(':')[0]
    scp_command = f"scp user@{server_host}:{staging_dir}/{zip_filename} ./"

    return jsonify({
        "status": "success",
        "original_filename": filename_to_search,
        "download_command": scp_command
    })


@app.route('/retrieve', methods=['GET'])
def retrieve_file():
    """
    Endpoint to retrieve a file based on an encrypted key.
    URL: /retrieve?key=<encrypted_key>
    """
    encrypted_key = request.args.get('key')
    
    if not encrypted_key:
        return jsonify({"error": "Missing 'key' parameter"}), 400

    # 1. Decrypt the filename
    filename = decrypt_filename(encrypted_key, app.config['SECRET_KEY'])
    
    if not filename:
        return jsonify({"error": "Invalid key or decryption failed"}), 400

    # 2. Find the file in the search paths
    search_paths = app.config['SEARCH_PATHS']
    found_path = find_file(filename, search_paths)
    
    if not found_path:
        return jsonify({"error": "File not found in any storage location"}), 404

    # 3. Process the file (move to staging and zip)
    staging_dir = app.config['STAGING_DIR']
    zip_filename = process_file_retrieval(found_path, staging_dir)
    
    if not zip_filename:
        return jsonify({"error": "Failed to process the file"}), 500

    # 4. Generate the SCP command response
    # Assuming the server is accessed via IP or hostname, we'll genericize it.
    # In a real scenario, you use request.host or a configured hostname.
    server_host = request.host.split(':')[0] 
    # Use a dummy user path or the actual path if known. 
    # The requirement says: "output perintah scp untuk mendownlod file tersebut dari server"
    # We will assume the user running the command has SSH access to the staging dir location
    
    # Constructing the SCP command
    # scp user@server:/home/scpkan/unique_name.zip ./
    
    scp_command = f"scp user@{server_host}:{staging_dir}/{zip_filename} ./"

    return jsonify({
        "status": "success",
        "message": "File prepared successfully",
        "original_filename": filename,
        "download_command": scp_command
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to upload a file.
    Form Data: 'file', 'nomor_surat'
    Behavior:
    1. Save file to random location.
    2. Encrypt filename (to generate 'encrip' key).
    3. Insert into DB (no_surat, path, encrip).
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    nomor_surat = request.form.get('nomor_surat')
    
    if file.filename == '' or not nomor_surat:
        return jsonify({"error": "No selected file or missing nomor_surat"}), 400

    # 1. Save Randomly
    search_paths = app.config['SEARCH_PATHS']
    saved_path = save_file_randomly(file, search_paths)
    
    if not saved_path:
        return jsonify({"error": "Failed to save file"}), 500

    # 2. Encrypt Key (for legacy compatibility)
    filename = os.path.basename(saved_path)
    encrypted_key = encrypt_filename(filename, app.config['SECRET_KEY'])
    
    # 3. Insert into Database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO surat (no_surat, path, encrip) VALUES (%s, %s, %s)"
        val = (nomor_surat, saved_path, encrypted_key)
        
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "File uploaded and stored safely",
            "stored_path": saved_path
        })
        
    except Exception as e:
        print(f"DB Insert Error: {e}")
        return jsonify({"error": f"Database error during insertion: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
