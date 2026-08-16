import sqlite3

conn = sqlite3.connect("eco_buddy.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO users (username, email, password_hash)
VALUES
('alice', 'alice@test.com', 'demo'),
('bob', 'bob@test.com', 'demo'),
('charlie', 'charlie@test.com', 'demo')
""")

cursor.execute("""
INSERT INTO assessments (user_id, eco_score)
VALUES
(1, 92),
(2, 85),
(3, 78)
""")

conn.commit()
conn.close()

print("Seed data added.")
