from flask import Flask, request, jsonify, send_from_directory, send_file, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os, shutil, zipfile, uuid, datetime

# Load .env config
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN", "changeme")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# === Configuration ===
UPLOAD_FOLDER = 'uploads'
ICON_FOLDER = 'static/icons'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# === Auth Decorators ===
def token_required(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if auth != f'Bearer {API_TOKEN}':
            return jsonify({'error': 'Unauthorized'}), 401
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
@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# === Run ===
if __name__ == '__main__':
    app.run(debug=True)
