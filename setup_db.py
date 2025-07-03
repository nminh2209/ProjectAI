# setup_db.py
import sqlite3

conn = sqlite3.connect('qa.db')
c = conn.cursor()

# Table to store previously answered questions with embeddings
c.execute('''
CREATE TABLE IF NOT EXISTS qa_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding TEXT NOT NULL
)
''')

# Optional: create a user table if not already created
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("✅ Database initialized.")
