from flask import Flask, request, jsonify, send_from_directory, send_file, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os, shutil, zipfile, uuid, datetime, json

# Load .env config
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN", "changeme")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")

application = Flask(__name__)
app = application  

app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# === Configuration ===
UPLOAD_FOLDER = 'uploads'
ICON_FOLDER = 'static/icons'
MOCK_FILE = 'mocks/mocks.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('mocks', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === Icon Mapping ===
EXT_ICON_MAP = {
    'pdf': 'pdf.png',
    'zip': 'winrar.png', 'rar': 'winrar.png', '7z': 'winrar.png',
    'jpg': 'image.png', 'jpeg': 'image.png', 'png': 'image.png', 'gif': 'image.png', 'webp': 'image.png', 'svg': 'image.png',
    'mp3': 'audio.png', 'wav': 'audio.png', 'ogg': 'audio.png', 'flac': 'audio.png',
    'mp4': 'video.png', 'webm': 'video.png', 'mkv': 'video.png', 'mov': 'video.png', 'avi': 'video.png',
    'py': 'python.png', 'js': 'javascript.png', 'ts': 'typescript.png', 'html': 'html.png', 'css': 'css.png',
    'json': 'json.png', 'xml': 'xml.png', 'php': 'php.png', 'java': 'java.png', 'c': 'c.png', 'cpp': 'cpp.png',
    'txt': 'text.png', 'md': 'markdown.png', 'doc': 'word.png', 'docx': 'word.png',
    'xls': 'excel.png', 'xlsx': 'excel.png', 'ppt': 'powerpoint.png', 'pptx': 'powerpoint.png',
}

def get_icon_for_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return f"/{ICON_FOLDER}/{EXT_ICON_MAP.get(ext, 'file.png')}"

def get_file_type(filename):
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'inconnu'

def load_mocks():
    if not os.path.exists(MOCK_FILE):
        with open(MOCK_FILE, 'w') as f:
            json.dump({}, f)
    with open(MOCK_FILE, 'r') as f:
        return json.load(f)

def save_mocks(mocks):
    with open(MOCK_FILE, 'w') as f:
        json.dump(mocks, f, indent=2)

# === Auth Decorators ===
def token_required(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if auth != f'Bearer {API_TOKEN}':
            return jsonify({'error': 'Unauthorized', "faulty_token": auth}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# === Web Auth ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Identifiants invalides')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# === Web Interface ===
@app.route('/')
@login_required
def dashboard():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_infos = []
    for fname in files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        icon_path = get_icon_for_file(fname)
        uploaded_ts = os.path.getmtime(path)
        uploaded_str = datetime.datetime.fromtimestamp(uploaded_ts).strftime('%d/%m/%Y %H:%M')
        file_infos.append({
            'name': fname,
            'size': os.path.getsize(path),
            'url': url_for('serve_file', filename=fname),
            'icon': icon_path,
            'type': get_file_type(fname),
            'uploaded': uploaded_str,
            'timestamp': uploaded_ts
        })
    return render_template('dashboard.html', files=file_infos, api_token=API_TOKEN)

@app.route('/mocks')
@login_required
def mock_editor():
    return render_template('mocks.html')

# === Mock API Logic ===
@app.route("/api/mock/<path:subpath>", methods=["OPTIONS"])
def mock_cors_preflight(subpath):
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

from flask import make_response, jsonify, request

@app.route('/api/mock/<path:subpath>', methods=['GET', 'POST'])
def serve_mock(subpath):
    full_path = f"/api/mock/{subpath}"
    mocks = load_mocks()

    if full_path in mocks and request.method == mocks[full_path].get("method", "GET"):
        response = make_response(jsonify(mocks[full_path].get("response", {})))
    else:
        response = make_response(jsonify({"error": "NOT FOUND"}), 400)

    # CORS headers : autoriser tout le monde
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    return response


@app.route('/api/admin/mock', methods=['POST'])
@token_required
def create_mock():
    return create_mock_core()

@app.route('/admin/mock', methods=['POST'])
@login_required
def create_mock_session():
    return create_mock_core()

@app.route('/api/admin/mock/<path:subpath>', methods=['DELETE'])
@token_required
def delete_mock(subpath):
    return delete_mock_core(subpath)

@app.route('/admin/mock/<path:subpath>', methods=['DELETE'])
@login_required
def delete_mock_session(subpath):
    return delete_mock_core(subpath)

@app.route('/admin/mocks.json')
@login_required
def get_mocks_json():
    return jsonify(load_mocks())


def create_mock_core():
    data = request.json
    path = data.get('path')
    method = data.get('method', 'GET').upper()
    response = data.get('response')

    if not path or not response:
        return jsonify({"error": "Path and response are required"}), 400

    if not path.startswith("/api/mock/"):
        return jsonify({"error": "Path must start with /api/mock/"}), 400

    mocks = load_mocks()
    mocks[path] = {"method": method, "response": response}
    save_mocks(mocks)
    return jsonify({"message": "Mock added", "path": path})

def delete_mock_core(subpath):
    full_path = f"/api/mock/{subpath}"
    mocks = load_mocks()
    if full_path in mocks:
        del mocks[full_path]
        save_mocks(mocks)
        return jsonify({"message": "Mock deleted"})
    return jsonify({"error": "Mock not found"}), 404
    

# === API Routes ===
@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    original_filename = secure_filename(file.filename)
    ext = os.path.splitext(original_filename)[1]
    unique_id = uuid.uuid4().hex
    new_filename = f"{unique_id}{ext}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    file.save(save_path)

    file_url = request.host_url.rstrip('/') + url_for('serve_file', filename=new_filename)
    return jsonify({'message': 'File uploaded successfully', 'url': file_url, 'id': unique_id, 'filename': new_filename})

@app.route('/api/files', methods=['GET'])
@token_required
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_infos = []
    for fname in files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        file_infos.append({
            'name': fname,
            'size': os.path.getsize(path),
            'url': request.host_url.rstrip('/') + url_for('serve_file', filename=fname)
        })
    return jsonify(file_infos)

@app.route('/api/delete/<filename>', methods=['DELETE'])
@token_required
def delete_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted'})
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/backup', methods=['GET'])
@token_required
def backup():
    zip_path = 'backup.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, app.config['UPLOAD_FOLDER'])
                zipf.write(filepath, arcname)
    return send_file(zip_path, as_attachment=True)

# === Public file access ===
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://learn.pierre-godino.com",
    "https://www.learn.pierre-godino.com",
]

@app.route('/files/<filename>')
def serve_file(filename):
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    response.headers["Content-Disposition"] = "attachment"
    return response


# === Run ===
if __name__ == '__main__':
    app.run(debug=True)
