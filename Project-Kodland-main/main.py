# ------- Импорти --------

from itsdangerous import URLSafeTimedSerializer
import random
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Entry 

app = Flask(__name__)
app.secret_key = 'somethingreallyandverysecretkeylmao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'

db.init_app(app)

with app.app_context():
    db.create_all()

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='yourapp@gmail.com',
    MAIL_PASSWORD='your-email-password',
)

# ------- Формы ---------

class RegisterForm(FlaskForm):
    gmail = StringField('Gmail', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

# ------ Роути --------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

s = URLSafeTimedSerializer(app.secret_key)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(gmail=form.gmail.data).first():
            flash(f"This account with email {form.gmail.data} already exists", 'error')
            return render_template('register.html', form=form)

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            gmail=form.gmail.data,
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not check_password_hash(user.password, form.password.data):
            flash('Incorrect username or password', 'error')
            return render_template('login.html', form=form)
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.created_at.desc()).all()
    return render_template('dashboard.html', username=session.get('username'), entries=entries)

@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_entry = Entry(user_id=session['user_id'], title=title, content=content)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('new_entry.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
