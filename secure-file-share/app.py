from flask import Flask, request, render_template, send_file
from cryptography.fernet import Fernet
import os
import json
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
KEY_FILE = 'secret.key'
HASH_FILE = 'file_hashes.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Ensure upload folder exists ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- AES Key Management ---
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        print("New encryption key generated.")
    else:
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
        print("Encryption key loaded.")
    return key

fernet = Fernet(load_key())

# --- SHA256 Hashing ---
def hash_data(data):
    return hashlib.sha256(data).hexdigest()

# --- Hash Storage Management ---
def load_hashes():
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE, 'r') as f:
        return json.load(f)

def save_hash(filename, hash_value):
    hashes = load_hashes()
    hashes[filename] = hash_value
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    data = file.read()
    encrypted_data = fernet.encrypt(data)
    file_hash = hash_data(data)

    filename = file.filename + '.enc'
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, 'wb') as f:
        f.write(encrypted_data)

    save_hash(filename, file_hash)

    return f'''
        <h3>File "{file.filename}" uploaded and encrypted successfully!</h3>
        <p><b>SHA256 Hash:</b> {file_hash}</p>
        <p><a href="/">Upload Another</a> | <a href="/files">View Files</a></p>
    '''

@app.route('/files')
def list_files():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.enc')]
    return render_template('files.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    encrypted_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        return f"Decryption failed: {str(e)}"

    # Integrity check
    expected_hash = load_hashes().get(filename)
    actual_hash = hash_data(decrypted_data)

    if expected_hash != actual_hash:
        return f'''
            <h3>⚠️ File integrity check failed!</h3>
            <p><b>Expected:</b> {expected_hash}</p>
            <p><b>Actual:</b> {actual_hash}</p>
            <p>This file may have been tampered with.</p>
        '''

    # Save decrypted file temporarily
    original_name = filename.replace('.enc', '')
    temp_path = os.path.join(UPLOAD_FOLDER, 'temp_' + original_name)
    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    response = send_file(temp_path, as_attachment=True)

    @response.call_on_close
    def cleanup():
        os.remove(temp_path)

    return response

# ----------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
