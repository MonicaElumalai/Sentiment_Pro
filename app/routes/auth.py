"""app/routes/auth.py — Login / Register / Logout"""
import re, random
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.database import get_db

auth_bp = Blueprint('auth', __name__)
EMAIL_RE = re.compile(r'^[\w.\-+]+@[\w\-]+\.[a-z]{2,}$', re.IGNORECASE)
COLORS   = ['#4f46e5','#0891b2','#059669','#dc2626','#d97706','#7c3aed','#db2777','#0284c7']


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard') if session.get('is_admin') else url_for('user.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session and not session.get('is_admin'):
        return redirect(url_for('user.dashboard'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pwd   = request.form.get('password','')
        db    = get_db()
        user  = db.execute('SELECT * FROM users WHERE username=? AND is_admin=0',(uname,)).fetchone()
        if user and check_password_hash(user['password_hash'], pwd):
            session.clear()
            session.update({'user_id': user['id'], 'username': user['username'],
                            'avatar_color': user['avatar_color'], 'is_admin': False})
            db.execute("UPDATE users SET last_login=datetime('now') WHERE id=?",(user['id'],))
            db.commit()
            flash(f'Welcome back, {uname}! 👋','success')
            return redirect(url_for('user.dashboard'))
        flash('Invalid username or password.','danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        pwd   = request.form.get('password','')
        cpwd  = request.form.get('confirm_password','')
        errs  = []
        if len(uname) < 3:         errs.append('Username must be ≥ 3 characters.')
        if not EMAIL_RE.match(email): errs.append('Invalid email address.')
        if len(pwd) < 6:           errs.append('Password must be ≥ 6 characters.')
        if pwd != cpwd:            errs.append('Passwords do not match.')
        if errs:
            for e in errs: flash(e,'danger')
            return render_template('auth/register.html', username=uname, email=email)
        db = get_db()
        if db.execute('SELECT id FROM users WHERE username=?',(uname,)).fetchone():
            flash('Username already taken.','danger')
            return render_template('auth/register.html', email=email)
        if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
            flash('Email already registered.','danger')
            return render_template('auth/register.html', username=uname)
        db.execute('INSERT INTO users (username,email,password_hash,avatar_color) VALUES (?,?,?,?)',
                   (uname, email, generate_password_hash(pwd), random.choice(COLORS)))
        db.commit()
        flash('Account created! Please sign in.','success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out.','info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pwd   = request.form.get('password','')
        db    = get_db()
        user  = db.execute('SELECT * FROM users WHERE username=? AND is_admin=1',(uname,)).fetchone()
        if user and check_password_hash(user['password_hash'], pwd):
            session.clear()
            session.update({'user_id': user['id'], 'username': user['username'],
                            'avatar_color': user['avatar_color'], 'is_admin': True})
            db.execute("UPDATE users SET last_login=datetime('now') WHERE id=?",(user['id'],))
            db.commit()
            flash('Admin access granted. Welcome!','success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid admin credentials.','danger')
    return render_template('auth/admin_login.html')
