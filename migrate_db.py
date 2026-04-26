import sqlite3
import os

DB_PATH = "social_posts.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found. It will be created when you run api.py")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ─── Migrate posts table ───────────────────────────────────────
    columns_to_add = [
        ("angle", "TEXT"),
        ("image_url", "TEXT"),
        ("image_path", "TEXT"),
        ("scheduled_at", "DATETIME"),
        ("likes_count", "INTEGER DEFAULT 0"),
        ("comments_count", "INTEGER DEFAULT 0"),
        ("post_url", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")
            print(f"[+] posts: Added column: {col_name}")
        except sqlite3.OperationalError:
            print(f"[-] posts: Column already exists: {col_name}")

    # ─── Create comments table ──────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            comment_text TEXT,
            author TEXT,
            auto_reply TEXT,
            replied INTEGER DEFAULT 0,
            replied_at DATETIME,
            reply_published INTEGER DEFAULT 0
        )
    ''')
    print("[+] comments: Table ensured.")

    conn.commit()
    conn.close()
    print("[*] Migration complete.")

if __name__ == "__main__":
    migrate()
