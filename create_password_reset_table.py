"""
Create password_reset_tokens table if it doesn't exist
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

print("=" * 60)
print("Creating password_reset_tokens table")
print("=" * 60)

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='password_reset_tokens'
    """)
    
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("Table 'password_reset_tokens' already exists.")
    else:
        # Create password_reset_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              token TEXT UNIQUE NOT NULL,
              expires_at TEXT NOT NULL,
              used INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token 
            ON password_reset_tokens(token);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id 
            ON password_reset_tokens(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at 
            ON password_reset_tokens(expires_at);
        """)
        
        conn.commit()
        
        print("SUCCESS: Table 'password_reset_tokens' created successfully!")
        print("Indexes created successfully!")
        
except sqlite3.Error as e:
    print(f"ERROR: Database error - {e}")
    conn.rollback()
finally:
    conn.close()

print("=" * 60)
input("Press Enter to exit...")


