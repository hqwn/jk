import streamlit as st
import sqlite3
import re
import time
from datetime import datetime
import pandas as pd

# DB setup
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    color TEXT DEFAULT 'white',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS banned_users (
    username TEXT PRIMARY KEY
)
""")
conn.commit()

BAD_WORDS = ["fuck", "shit", "bitch", "asshole", "dick"]

# Censoring logic
def build_obfuscated_pattern(word):
    pattern = ''.join([re.escape(letter) + r'\s*[^a-zA-Z0-9]*' for letter in word])
    return pattern.rstrip(r'\s*[^a-zA-Z0-9]*')

def censor_text(text):
    for word in BAD_WORDS:
        pattern = build_obfuscated_pattern(word)
        text = re.sub(pattern, lambda m: '*' * len(word), text, flags=re.IGNORECASE)
    return text

def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()
    delete_old_messages()

def get_messages(limit=20):
    c.execute("SELECT id, username, message, color, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return c.fetchall()

def is_banned(username):
    c.execute("SELECT 1 FROM banned_users WHERE username=?", (username,))
    return c.fetchone() is not None

def ban_user(username):
    c.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    conn.commit()

def unban_user(username):
    c.execute("DELETE FROM banned_users WHERE username=?", (username,))
    conn.commit()

def clear_chat():
    c.execute("DELETE FROM messages")
    conn.commit()

def delete_message_by_id(msg_id):
    c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()

def delete_old_messages():
    c.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 20)")
    conn.commit()

# Auth
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "slow_mode" not in st.session_state:
    st.session_state.slow_mode = False

if not st.session_state.username:
    username = st.text_input("Enter your username:")
    if username:
        if username.lower() == "aryan":
            pwd = st.text_input("Enter admin password:", type="password")
            if pwd == "thisisnotmypassword":
                st.session_state.admin_authenticated = True
                st.session_state.username = "aryan"
            else:
                st.warning("Incorrect password")
                st.stop()
        else:
            if is_banned(username):
                st.error("You are banned from this chat.")
                st.stop()
            st.session_state.username = username.strip()

st.title("📡 SQLite Real-time Chat Room")

# --- ADMIN PANEL ---
if st.session_state.username == "aryan" and st.session_state.admin_authenticated:
    st.subheader("🔧 Admin Panel")

    col1, col2 = st.columns(2)
    with col1:
        ban_target = st.text_input("Ban user:")
        if st.button("Ban") and ban_target:
            ban_user(ban_target)
            st.success(f"Banned '{ban_target}'")
    
    with col2:
        unban_target = st.text_input("Unban user:")
        if st.button("Unban") and unban_target:
            unban_user(unban_target)
            st.success(f"Unbanned '{unban_target}'")

    col3, col4 = st.columns(2)
    with col3:
        msg_id = st.text_input("Delete message by ID:")
        if st.button("Delete Msg") and msg_id.isdigit():
            delete_message_by_id(int(msg_id))
            st.success(f"Deleted message ID {msg_id}")
    with col4:
        if st.button("Clear All Chat"):
            clear_chat()
            st.success("Chat cleared.")

    # Slow mode toggle
    st.session_state.slow_mode = st.checkbox("🐢 Enable Slow Mode (3s delay)", value=st.session_state.slow_mode)

    # Download chat history
    if st.button("📥 Download Chat History"):
        c.execute("SELECT * FROM messages ORDER BY id")
        df = pd.DataFrame(c.fetchall(), columns=["ID", "Username", "Message", "Color", "Timestamp"])
        st.download_button("Download as CSV", df.to_csv(index=False), file_name="chat_history.csv", mime="text/csv")

# --- Chat Input ---
admin_color = st.color_picker("Pick admin message color", "#FFD700") if st.session_state.username == "aryan" else None

with st.form(key="message_form", clear_on_submit=True):
    message = st.chat_input("Your message:")
    submit = st.form_submit_button("Send")

if submit and message.strip():
    color = admin_color if st.session_state.username == "aryan" else "white"
    add_message(st.session_state.username, message.strip(), color)
    if st.session_state.slow_mode:
        time.sleep(3)
    st.rerun()

# --- Chat Display ---
st.subheader("📜 Chat History (latest first)")
msgs = get_messages()

if msgs:
    for mid, username, msg, color, ts in msgs:
        t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        user_display = f"<span style='color:{color}; font-weight:bold;'>[{t}] {username}:</span>"
        msg_display = f"<span style='color:white'>{msg}</span>" if username.lower() != "aryan" else f"<span style='color:{color}'>{msg}</span>"
        st.markdown(f"{user_display} {msg_display}", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# Auto refresh every 2s
time.sleep(2)
st.rerun()
