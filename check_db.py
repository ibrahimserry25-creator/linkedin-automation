import sqlite3
conn = sqlite3.connect('social_posts.db')
c = conn.cursor()

# Check posts statuses
print("=== All statuses ===")
c.execute("SELECT status, COUNT(*) FROM posts GROUP BY status")
for r in c.fetchall():
    print(r)

print("\n=== Posts with URLs ===")
c.execute("SELECT id, status, substr(post_url,1,60) FROM posts WHERE post_url IS NOT NULL AND post_url != '' LIMIT 10")
for r in c.fetchall():
    print(r)

conn.close()
