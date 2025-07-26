import streamlit as st
import sqlite3
from datetime import datetime

# === DB ===
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# === Tables ===
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

# === DB functions ===

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

# === APP ===

st.title("📡 SQLite Real-time Chat Room")

tab1, tab2 = st.tabs(["Chat", "Admin"])

with tab1:
    if "username" not in st.session_state or not st.session_state.username:
        username = st.text_input("Enter your name to join:")
        if username:
            st.session_state.username = username.strip()
        else:
            st.stop()

    if is_banned(st.session_state.username):
        st.error("🚫 You are banned from this chat.")
        st.stop()

    message = st.text_input("Your message:")

    if st.button("Send"):
        if message.strip():
            add_message(st.session_state.username, message.strip())
            st.rerun()

    if st.button("Clear All Messages"):
        clear_messages()
        st.success("All messages cleared.")
        st.rerun()


    st.subheader("Chat History (latest first):")
    msgs = get_messages()
    
    if msgs:
        for username, msg, ts in msgs:
            st.write(f"**[{ts.split('.')[0]}] {username}:** {msg}")
    else:
        st.info("No messages yet.")
    time.sleep(2)
    st.rerun()
with tab2:
    st.subheader("Admin")
    user_to_ban = st.text_input("Ban a username:")
    if st.button("Ban User") and user_to_ban.strip():
        ban_user(user_to_ban.strip())
        st.success(f"{user_to_ban} has been banned!")

    st.write("Banned users:")
    banned = get_banned_users()
    st.write(banned if banned else "None")
