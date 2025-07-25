import streamlit as st
import sqlite3
from datetime import datetime

# === DB SETUP ===

DB_FILE = "chat.db"

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
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

# === STREAMLIT ===

st.title("📡 SQLite Real-time Chat Room")

tabs = st.tabs(["Chat", "Admin"])

# === CHAT TAB ===

with tabs[0]:
    if "username" not in st.session_state or not st.session_state.username:
        username = st.text_input("Enter your username to join:")
        if username:
            st.session_state.username = username.strip()
        else:
            st.stop()

    if is_banned(st.session_state.username):
        st.error("🚫 You are banned from this chat.")
        st.stop()

    message = st.text_input("Your message:")

    if st.button("Send") and message.strip():
        add_message(st.session_state.username, message.strip())
        st.experimental_rerun()

    if st.button("Reset All Messages"):
        clear_messages()
        st.success("💣 All messages cleared.")
        st.experimental_rerun()

    st.experimental_autorefresh(interval=3000)

    st.subheader("Chat History (latest first):")
    messages = get_messages()

    for username, msg, ts in messages:
        st.write(f"**[{ts.split('.')[0]}] {username}:** {msg}")

# === ADMIN TAB ===

with tabs[1]:
    st.subheader("🚨 Admin Tools")

    user_to_ban = st.text_input("Ban a user by name:")

    if st.button("Ban User") and user_to_ban.strip():
        ban_user(user_to_ban.strip())
        st.success(f"{user_to_ban} has been banned.")

    st.write("Currently banned users:")
    banned_list = get_banned_users()
    st.write(banned_list if banned_list else "None")
