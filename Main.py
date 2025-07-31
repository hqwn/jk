import streamlit as st
import sqlite3
import re
import time
from datetime import datetime
import pandas as pd
import os

# --- Setup ---
CHAT_DB = "chat.db"
USER_DB = "users.db"

# DB connections
chat_conn = sqlite3.connect(CHAT_DB, check_same_thread=False)
user_conn = sqlite3.connect(USER_DB, check_same_thread=False)
chat_cursor = chat_conn.cursor()
user_cursor = user_conn.cursor()

# Chat table
chat_cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    color TEXT DEFAULT 'white',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

chat_cursor.execute("""
CREATE TABLE IF NOT EXISTS banned_users (
    username TEXT PRIMARY KEY
)
""")
chat_conn.commit()

# User table
user_cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
user_conn.commit()

# --- Censorship ---
BAD_WORDS = ["fuck", "shit", "bitch", "asshole", "dick"]

def build_obfuscated_pattern(word):
    return ''.join([re.escape(ch) + r'\s*[^a-zA-Z0-9]*' for ch in word])

def censor_text(text):
    for word in BAD_WORDS:
        pattern = build_obfuscated_pattern(word)
        text = re.sub(pattern, lambda m: '*' * len(word), text, flags=re.IGNORECASE)
    return text

# --- Chat functions ---
def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    chat_cursor.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    chat_conn.commit()
    delete_old_messages()

def get_messages(limit=50):
    chat_cursor.execute("SELECT id, username, message, color FROM messages ORDER BY id ASC LIMIT ?", (limit,))
    return chat_cursor.fetchall()

def delete_old_messages():
    chat_cursor.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 50)")
    chat_conn.commit()

def is_banned(username):
    chat_cursor.execute("SELECT 1 FROM banned_users WHERE username=?", (username,))
    return chat_cursor.fetchone() is not None

def ban_user(username):
    chat_cursor.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    chat_conn.commit()

def unban_user(username):
    chat_cursor.execute("DELETE FROM banned_users WHERE username=?", (username,))
    chat_conn.commit()

def clear_chat():
    chat_cursor.execute("DELETE FROM messages")
    chat_conn.commit()

def delete_message_by_id(msg_id):
    chat_cursor.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    chat_conn.commit()

# --- User account logic ---
def create_user(username):
    try:
        user_cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def user_exists(username):
    user_cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
    return user_cursor.fetchone() is not None

# --- Streamlit App Setup ---
st.set_page_config(page_title="💬 Login Chat", page_icon="💬", layout="wide")

if "username" not in st.session_state:
    with st.container():
        st.title("🔐 Login / Sign Up")
        choice = st.radio("Select Action", ["Sign Up", "Login"])
        uname = st.text_input("Username")

        if st.button(choice):
            if not uname.strip():
                st.warning("Username required")
                st.stop()

            if choice == "Sign Up":
                if user_exists(uname):
                    st.error("Username already taken.")
                elif is_banned(uname):
                    st.error("You're banned and can't re-use that name.")
                else:
                    if create_user(uname.strip()):
                        st.success("Account created. Welcome!")
                        st.session_state.username = uname.strip()
                        st.rerun()
            elif choice == "Login":
                if is_banned(uname):
                    st.error("You're banned.")
                    st.stop()
                elif user_exists(uname.strip()):
                    st.session_state.username = uname.strip()
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.warning("Username not found. Sign up first.")
        st.stop()

# --- Admin Panel ---
if st.session_state.username.lower() == "aryan":
    with st.sidebar:
        st.title("🛠 Admin Panel")
        ban_target = st.text_input("Ban user")
        if st.button("Ban") and ban_target:
            ban_user(ban_target)
            st.success(f"Banned {ban_target}")

        unban_target = st.text_input("Unban user")
        if st.button("Unban") and unban_target:
            unban_user(unban_target)
            st.success(f"Unbanned {unban_target}")

        msg_id = st.text_input("Delete message ID")
        if st.button("Delete Msg") and msg_id.isdigit():
            delete_message_by_id(int(msg_id))
            st.success(f"Deleted message ID {msg_id}")

        if st.button("🗑 Clear All Chat"):
            clear_chat()
            st.success("Chat cleared.")

        st.session_state.slow_mode = st.checkbox("🐢 Slow Mode (3s)", value=st.session_state.slow_mode)

# --- Chat UI ---
st.title("💬 Live Chat")

messages = get_messages()
for _, username, text, color in messages:
    avatar = "👤" if username != "aryan" else "🛠"
    with st.chat_message(username if username != "aryan" else "Admin", avatar=avatar):
        st.markdown(f"<div style='color:{color}'>{text}</div>", unsafe_allow_html=True)

# --- Chat Input ---
st.markdown("---")
msg_color = st.color_picker("Pick your color", "#FFD700") if st.session_state.username == "aryan" else "white"
msg = st.chat_input("Say something...")

if msg:
    add_message(st.session_state.username, msg.strip(), msg_color)
    if st.session_state.slow_mode:
        time.sleep(3)
    st.rerun()
