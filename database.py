import sqlite3

def get_db():
    return sqlite3.connect("attendance.db")

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    db.close()
