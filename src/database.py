import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "social_posts.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            angle TEXT,
            content TEXT,
            image_url TEXT,
            image_path TEXT,
            platform TEXT,
            status TEXT DEFAULT 'Generated',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            scheduled_at DATETIME,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            post_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_value (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_kv(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM key_value WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_kv(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO key_value (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def save_post(topic, angle, content, image_url, image_path, platform, status='Generated', scheduled_at=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO posts (topic, angle, content, image_url, image_path, platform, status, scheduled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (topic, angle, content, image_url, image_path, platform, status, scheduled_at))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_post_by_id(post_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_post_status(post_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()

def update_post_content(post_id, new_content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET content = ? WHERE id = ?", (new_content, post_id))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_post(post_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

def get_scheduled_posts():
    """Returns posts that are scheduled and ready to be published."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Find posts where scheduled_at is less than or equal to current time and status is 'Scheduled'
    cursor.execute("""
        SELECT id, topic, content, image_path, platform 
        FROM posts 
        WHERE status = 'Scheduled' AND scheduled_at <= datetime('now', 'localtime')
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_post_as_published(post_id, post_url=None):
    """Marks a post as published and updates the status and url."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if post_url:
        cursor.execute("UPDATE posts SET status = 'Published', post_url = ? WHERE id = ?", (post_url, post_id))
    else:
        cursor.execute("UPDATE posts SET status = 'Published' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
