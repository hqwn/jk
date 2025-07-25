import streamlit as st
import sqlite3

# === CONFIG ===
DB_FILE = "chat.db"

# === CONNECT DB ===
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# === CREATE TABLES ===
c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS banned_users (
        username TEXT PRIMARY KEY
    )
""")
conn.commit()

# === DB FUNCTIONS ===

def add_message(username, message):
    c.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()

def get_messages(limit=50):
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return c.fetchall()

def clear_messages():
    c.execute("DELETE FROM messages")
    conn.commit()

def ban_user(username):
    c.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    conn.commit()

def is_banned(username):
    c.execute("SELECT 1 FROM banned_users WHERE username = ?", (username,))
    return c.fetchone() is not None

def get_banned_users():
    c.execute("SELECT username FROM banned_users")
    return [row[0] for row in c.fetchall()]

# === STREAMLIT APP ===

st.title("📡 SQLite Real-time Chat Room")

tab1, tab2 = st.tabs(["Chat", "Admin"])

with tab1:
    # Username input
    if "username" not in st.session_state or not st.session_state.username:
        username = st.text_input("Enter your name to join:")
        if username:
            st.session_state.username = username.strip()
        else:
            st.stop()

    # Banned check
    if is_banned(st.session_state.username):
        st.error("🚫 You are banned from this chat.")
        st.stop()

    # Message input
    message = st.text_input("Type your message:")

    if st.button("Send"):
        if message.strip():
            add_message(st.session_state.user
