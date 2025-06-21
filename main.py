# 🌿 Простой сайт-дневник с Flask
# Возможности: регистрация, авторизация, добавление записей

from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'eco_diary_secret_key'

# --- Создание базы данных ---
def init_db():
    if not os.path.exists('eco_diary.db'):
        conn = sqlite3.connect('eco_diary.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

# --- Главная страница ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('eco_diary.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, content FROM entries WHERE user_id = ? ORDER BY id DESC', (session['user_id'],))
    entries = cursor.fetchall()
    conn.close()
    return render_template('index.html', entries=entries)

# --- Регистрация ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('eco_diary.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return 'Пользователь уже существует'
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# --- Вход ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('eco_diary.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return 'Неверный логин или пароль'
    return render_template('login.html')

# --- Добавление записи ---
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    date = request.form['date']

    conn = sqlite3.connect('eco_diary.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO entries (user_id, date, content) VALUES (?, ?, ?)',
                   (session['user_id'], date, content))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- Выход ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Запуск ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
