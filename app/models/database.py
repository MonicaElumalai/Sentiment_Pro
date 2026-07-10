"""
app/models/database.py  —  SQLite helpers for SentimentPro
Admin is auto-seeded on every init_db() call.
Default: username=admin  password=Admin@123
"""
import sqlite3, os
from flask import g
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'sentimentpro.db')


def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


def close_db(e=None):
    db = getattr(g, '_db', None)
    if db:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # ── Users table ──────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            avatar_color  TEXT    DEFAULT "#4f46e5",
            created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
            last_login    TEXT    DEFAULT NULL
        )
    ''')

    # ── Reviews table ─────────────────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id            INTEGER NOT NULL,
            review_text        TEXT    NOT NULL,
            overall_sentiment  TEXT    NOT NULL,
            overall_confidence REAL    NOT NULL,
            aspect_data        TEXT    DEFAULT NULL,
            is_mixed           INTEGER DEFAULT 0,
            source             TEXT    DEFAULT "manual",
            created_at         TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # ── Safe migrations for older DBs ─────────────────────────────────────────
    for tbl, col, defn in [
        ('users',   'avatar_color', 'TEXT DEFAULT "#4f46e5"'),
        ('users',   'last_login',   'TEXT DEFAULT NULL'),
        ('reviews', 'aspect_data',  'TEXT DEFAULT NULL'),
        ('reviews', 'is_mixed',     'INTEGER DEFAULT 0'),
        ('reviews', 'source',       'TEXT DEFAULT "manual"'),
    ]:
        try:
            c.execute(f'ALTER TABLE {tbl} ADD COLUMN {col} {defn}')
        except Exception:
            pass   # column already exists

    # ── Seed / update admin credentials ──────────────────────────────────────
    pw = generate_password_hash('Admin@123')

    existing = c.execute(
        "SELECT id FROM users WHERE username='admin'"
    ).fetchone()

    if existing:
        # Always keep admin password and is_admin flag correct
        c.execute(
            "UPDATE users SET password_hash=?, is_admin=1, email='admin@sentimentpro.com' WHERE username='admin'",
            (pw,)
        )
    else:
        c.execute(
            '''INSERT INTO users (username, email, password_hash, is_admin, avatar_color)
               VALUES ('admin', 'admin@sentimentpro.com', ?, 1, '#7c3aed')''',
            (pw,)
        )

    conn.commit()
    conn.close()
    print('[DB] Initialised. Admin: admin / Admin@123')
