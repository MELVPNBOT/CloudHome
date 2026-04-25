import os
import json
import base64
import random
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session
from github import Github

app = Flask(__name__)
app.secret_key = "cloud_home_super_secret"

# ДАННЫЕ ГИТХАБА
TOKEN = "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"
REPO_NAME = "MELVPNBOT/CloudHome"
DB_PATH = "db.json"

g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

# --- УТИЛИТЫ ---
def get_db():
    f = repo.get_contents(DB_PATH)
    data = json.loads(base64.b64decode(f.content).decode('utf-8'))
    return data, f.sha

def save_db(data, sha):
    repo.update_file(DB_PATH, "update db", json.dumps(data, indent=4), sha)

def get_captcha():
    a, b = random.randint(10, 99), random.randint(1, 20)
    session['captcha_ans'] = a + b
    return f"{a} + {b}"

# --- МАРШРУТЫ ---
@app.route('/')
def index():
    if 'user' in session: return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if int(request.form['captcha']) != session.get('captcha_ans'):
            return "Ошибка капчи!"
        
        user = request.form['user']
        pw = hashlib.sha256(request.form['pw'].encode()).hexdigest()
        
        db, sha = get_db()
        if user in db: return "Юзер уже есть!"
        
        db[user] = {"password": pw}
        save_db(db, sha)
        # Создаем папку юзера
        repo.create_file(f"{user}/.init", "init", "", branch="main")
        return redirect('/login')
    
    return render_template('register.html', captcha=get_captcha())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        pw = hashlib.sha256(request.form['pw'].encode()).hexdigest()
        db, _ = get_db()
        if user in db and db[user]['password'] == pw:
            session['user'] = user
            return redirect('/dashboard')
        return "Неверно!"
    return render_template('login.html', captcha=get_captcha())

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user_dir = session['user']
    files = repo.get_contents(user_dir)
    return render_template('dashboard.html', files=[f for f in files if f.name != ".init"])

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        path = f"{session['user']}/{file.filename}"
        repo.create_file(path, f"upload {file.filename}", file.read())
    return redirect('/dashboard')

@app.route('/delete/<path:name>')
def delete(name):
    path = f"{session['user']}/{name}"
    f = repo.get_contents(path)
    repo.delete_file(f.path, "delete", f.sha)
    return redirect('/dashboard')

@app.route('/edit/<path:name>', methods=['GET', 'POST'])
def edit(name):
    path = f"{session['user']}/{name}"
    f = repo.get_contents(path)
    if request.method == 'POST':
        new_content = request.form['content']
        repo.update_file(f.path, "edit", new_content, f.sha)
        return redirect('/dashboard')
    
    content = base64.b64decode(f.content).decode('utf-8')
    return render_template('edit.html', name=name, content=content)

@app.route('/rename', methods=['POST'])
def rename():
    old_name = request.form['old']
    new_name = request.form['new']
    user = session['user']
    
    # В GitHub API "переименование" — это копирование и удаление старого
    old_f = repo.get_contents(f"{user}/{old_name}")
    repo.create_file(f"{user}/{new_name}", "rename", base64.b64decode(old_f.content))
    repo.delete_file(old_f.path, "remove old after rename", old_f.sha)
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)
