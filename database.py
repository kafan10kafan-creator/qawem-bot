import sqlite3
import os

DB_PATH = "qawem_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        level TEXT,
        streak INTEGER DEFAULT 1,
        last_goals TEXT,
        points INTEGER DEFAULT 0,
        is_allowed INTEGER DEFAULT 0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # جدول الإعدادات (مثل OWNER_ID)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def add_user_db(user_id, name=None, level="medium", is_allowed=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO users (user_id, name, level, is_allowed)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
    name = COALESCE(?, name),
    level = COALESCE(?, level),
    is_allowed = ?
    ''', (user_id, name, level, is_allowed, name, level, is_allowed))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "user_id": user[0],
            "name": user[1],
            "level": user[2],
            "streak": user[3],
            "last_goals": user[4],
            "points": user[5],
            "is_allowed": user[6]
        }
    return None

def update_streak(user_id, increment=1):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET streak = streak + ?, points = points + 10 WHERE user_id = ?", (increment, user_id))
    conn.commit()
    conn.close()

def get_allowed_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE is_allowed = 1")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(users)

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized!")

def add_points(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, points FROM users WHERE is_allowed = 1 ORDER BY points DESC LIMIT 5")
    top_users = cursor.fetchall()
    conn.close()
    return top_users
