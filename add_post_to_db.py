import sqlite3

conn = sqlite3.connect('social_posts.db')
c = conn.cursor()

POST_URL = "https://www.linkedin.com/posts/ibrahim-ismail01_%D8%A7%D9%86%D8%B4%D8%B1-%D8%A3%D9%87%D9%85%D9%8A%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D9%84-%D8%A7%D9%84%D8%AC%D9%85%D8%A7%D8%B9%D9%8A-share-7454701727682895873-oZtf"

c.execute("SELECT id FROM posts WHERE post_url LIKE ?", ('%7454701727682895873%',))
existing = c.fetchone()
print('Existing:', existing)

if existing:
    c.execute("UPDATE posts SET status='Published', created_at=datetime('now','localtime') WHERE id=?", (existing[0],))
    print(f"Updated post ID {existing[0]} to Published")
else:
    c.execute(
        "INSERT INTO posts (topic, platform, content, status, post_url, created_at) VALUES (?,?,?,?,?,datetime('now','localtime'))",
        ('العمل الجماعي', 'linkedin', 'انشر اهمية العمل الجماعي', 'Published', POST_URL)
    )
    print(f"Inserted new post ID {c.lastrowid}")

conn.commit()

print("\n=== Published posts ===")
c.execute("SELECT id, status, substr(post_url,1,70), created_at FROM posts WHERE status='Published'")
for r in c.fetchall():
    print(r)

conn.close()
print("Done!")
