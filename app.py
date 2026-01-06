from flask import Flask, request, jsonify, render_template
from config import Config
from utils import decrypt_data, find_files_in_paths, process_file_retrieval, save_file_to_dir, encrypt_data
import os
import mysql.connector
import random

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
    Endpoint to search for files via the web UI using 'nomor_surat'.
    Input JSON: { "filename": "SK/..." } (Nomor Surat)
    """
    data = request.get_json()
    query_input = data.get('filename') # 'filename' key is used for Nomor Surat input
    
    if not query_input:
        return jsonify({"error": "Nomor Surat is required"}), 400
    
    filenames = []
    
    # 1. Database Lookup (Get Encrypted List)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # We need the 'encrip' column which holds the list of filenames
        cursor.execute("SELECT encrip FROM surat WHERE no_surat = %s LIMIT 1", (query_input,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            encrypted_key = result[0]
            # Decrypt to get the list of filenames
            filenames = decrypt_data(encrypted_key, app.config['SECRET_KEY'])
            if not filenames:
                return jsonify({"error": "Failed to decrypt file data"}), 500
        else:
            # Fallback: maybe they entered a direct filename?
            # Supporting direct filename search might be tricky with multiple files logic.
            # Let's treat it as a single file list if no DB match.
            filenames = [query_input]
            
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database connection failed"}), 500

    # 2. Find the files (System Search)
    search_paths = app.config['SEARCH_PATHS']
    found_paths = find_files_in_paths(filenames, search_paths)
    
    if not found_paths:
        return jsonify({"error": "Files not found in storage"}), 404

    # 3. Process (zip multiple files)
    staging_dir = app.config['STAGING_DIR']
    zip_filename = process_file_retrieval(found_paths, staging_dir)
    
    if not zip_filename:
        return jsonify({"error": "System error: Failed to process files"}), 500

    # 4. Generate SCP Command
    server_host = request.host.split(':')[0]
    scp_command = f"scp user@{server_host}:{staging_dir}/{zip_filename} ./"

    return jsonify({
        "status": "success",
        "original_filenames": filenames,
        "download_command": scp_command
    })


@app.route('/retrieve', methods=['GET'])
def retrieve_file():
    """
    Endpoint to retrieve files based on an encrypted key.
    URL: /retrieve?key=<encrypted_key>
    """
    encrypted_key = request.args.get('key')
    
    if not encrypted_key:
        return jsonify({"error": "Missing 'key' parameter"}), 400

    # 1. Decrypt the key -> List of filenames
    filenames = decrypt_data(encrypted_key, app.config['SECRET_KEY'])
    
    if not filenames:
        return jsonify({"error": "Invalid key or decryption failed"}), 400

    # 2. Find the files in the search paths
    search_paths = app.config['SEARCH_PATHS']
    found_paths = find_files_in_paths(filenames, search_paths)
    
    if not found_paths:
        return jsonify({"error": "Files not found in any storage location"}), 404

    # 3. Process the files (zip them)
    staging_dir = app.config['STAGING_DIR']
    zip_filename = process_file_retrieval(found_paths, staging_dir)
    
    if not zip_filename:
        return jsonify({"error": "Failed to process the files"}), 500

    # 4. Generate the SCP command response
    server_host = request.host.split(':')[0] 
    scp_command = f"scp user@{server_host}:{staging_dir}/{zip_filename} ./"

    return jsonify({
        "res": 200,
        "message": "Berhasil Decrypt!",
        "data": filenames,
        "scp_command": scp_command
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to upload multiple files.
    Form Data: 'file' (multiple), 'nomor_surat'
    Behavior:
    1. Select ONE random directory.
    2. Save ALL files there.
    3. Encrypt the LIST of filenames.
    4. Insert into DB (no_surat, path, encrip).
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    files = request.files.getlist('file')
    nomor_surat = request.form.get('nomor_surat')
    
    if not files or not nomor_surat:
        return jsonify({"error": "No selected files or missing nomor_surat"}), 400

    # 1. Select Random Directory
    search_paths = app.config['SEARCH_PATHS']
    if not search_paths:
        return jsonify({"error": "No search paths configured"}), 500
        
    target_dir = random.choice(search_paths)
    saved_filenames = []
    
    # 2. Save All Files
    try:
        for file in files:
            if file.filename == '':
                continue
            full_path = save_file_to_dir(file, target_dir)
            saved_filenames.append(os.path.basename(full_path))
            
        if not saved_filenames:
            return jsonify({"error": "No valid files saved"}), 400
            
    except Exception as e:
        print(f"File save error: {e}")
        return jsonify({"error": "Failed to save files locally"}), 500

    # 3. Encrypt List of Filenames
    encrypted_key = encrypt_data(saved_filenames, app.config['SECRET_KEY'])
    
    # 4. Insert into Database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store only the directory path
        directory_path = target_dir
        
        sql = "INSERT INTO surat (no_surat, path, encrip) VALUES (%s, %s, %s)"
        val = (nomor_surat, directory_path, encrypted_key)
        
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Files uploaded and stored safely",
            "stored_path": directory_path,
            "filenames": saved_filenames
        })
        
    except Exception as e:
        print(f"DB Insert Error: {e}")
        return jsonify({"error": f"Database error during insertion: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
