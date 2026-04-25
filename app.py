import os
import json
import base64
import random
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session
from github import Github, GithubException

app = Flask(__name__)
app.secret_key = "cloud_home_super_secret_key_123" # Любая случайная строка

# --- КОНФИГУРАЦИЯ ---
# Твой новый токен
TOKEN = "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"
REPO_NAME = "MELVPNBOT/CloudHome"
DB_PATH = "db.json"

try:
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    print(f"Ошибка подключения к GitHub: {e}")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_db():
    try:
        f = repo.get_contents(DB_PATH)
        data = json.loads(base64.b64decode(f.content).decode('utf-8'))
        return data, f.sha
    except Exception as e:
        print(f"Ошибка чтения базы данных: {e}")
        return {}, None

def save_db(data, sha):
    repo.update_file(DB_PATH, "update database", json.dumps(data, indent=4), sha)

def generate_captcha():
    a, b = random.randint(10, 99), random.randint(10, 99)
    session['captcha_ans'] = a + b
    return f"{a} + {b}"

# --- РОУТЫ (ЛОГИКА) ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Проверка капчи
        user_ans = request.form.get('captcha')
        if not user_ans or int(user_ans) != session.get('captcha_ans'):
            return "❌ Капча решена неверно! <a href='/register'>Назад</a>"
        
        username = request.form.get('user')
        password = hashlib.sha256(request.form.get('pw').encode()).hexdigest()
        
        db, sha = get_db()
        if username in db:
            return "❌ Такой пользователь уже есть!"
        
        db[username] = {"password": password}
        save_db(db, sha)
        
        # Создаем личную папку пользователя (через файл-маркер)
        repo.create_file(f"{username}/.init", "user init", "", branch="main")
        return redirect(url_for('login'))
    
    captcha_text = generate_captcha()
    return render_template('register.html', captcha=captcha_text)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('user')
        password = hashlib.sha256(request.form.get('pw').encode()).hexdigest()
        
        db, _ = get_db()
        if username in db and db[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return "❌ Неверный логин или пароль! <a href='/login'>Назад</a>"
    
    return render_template('login.html', captcha=generate_captcha())

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_dir = session['user']
    try:
        files = repo.get_contents(user_dir)
        # Фильтруем системный файл .init
        user_files = [f for f in files if f.name != ".init"]
    except:
        user_files = []
        
    return render_template('dashboard.html', files=user_files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session: return redirect(url_for('login'))
    file = request.files['file']
    if file:
        path = f"{session['user']}/{file.filename}"
        repo.create_file(path, f"Upload: {file.filename}", file.read())
    return redirect(url_for('dashboard'))

@app.route('/delete/<path:name>')
def delete(name):
    if 'user' not in session: return redirect(url_for('login'))
    path = f"{session['user']}/{name}"
    f = repo.get_contents(path)
    repo.delete_file(f.path, f"Delete: {name}", f.sha)
    return redirect(url_for('dashboard'))

@app.route('/rename', methods=['POST'])
def rename():
    if 'user' not in session: return redirect(url_for('login'))
    old_name = request.form.get('old')
    new_name = request.form.get('new')
    user = session['user']
    
    # В GitHub API переименование = Копирование + Удаление оригинала
    old_f = repo.get_contents(f"{user}/{old_name}")
    repo.create_file(f"{user}/{new_name}", f"Rename to {new_name}", base64.b64decode(old_f.content))
    repo.delete_file(old_f.path, f"Remove old {old_name}", old_f.sha)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
