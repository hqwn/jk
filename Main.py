import streamlit as st
import sqlite3
import re
import time
from datetime import datetime

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
    letters = list(word)
    pattern = r''
    for letter in letters:
        pattern += re.escape(letter) + r'\s*[^a-zA-Z0-9]*'
    return pattern.rstrip(r'\s*[^a-zA-Z0-9]*')

def censor_text(text):
    for word in BAD_WORDS:
        pattern = build_obfuscated_pattern(word)
        regex = re.compile(pattern, flags=re.IGNORECASE)
        text = regex.sub(lambda m: '*' * len(word), text)
    return text

# Chat DB ops
def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()
    delete_old_messages()

def get_messages(limit=20):
    c.execute("SELECT username, message, color, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return c.fetchall()

def is_banned(username):
    c.execute("SELECT 1 FROM banned_users WHERE username=?", (username,))
    return c.fetchone() is not None

def ban_user(username):
    c.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    conn.commit()

def clear_chat():
    c.execute("DELETE FROM messages")
    conn.commit()

def delete_old_messages():
    c.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 20)")
    conn.commit()

# Auth/login
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

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
    else:
        st.stop()

st.title("\U0001F4E1 SQLite Real-time Chat Room")

if st.session_state.username == "aryan" and st.session_state.admin_authenticated:
    st.subheader("\U0001F527 Admin Panel")
    ban_target = st.text_input("Ban a user (exact username):")
    if st.button("Ban User") and ban_target:
        ban_user(ban_target)
        st.success(f"User '{ban_target}' has been banned.")

    if st.button("Clear Chat"):
        clear_chat()
        st.success("Chat has been cleared.")

admin_color = st.color_picker("Pick admin message color", "#FFD700") if st.session_state.username == "aryan" else None

with st.form(key="message_form", clear_on_submit=True):
    message = st.text_input("Your message:")
    submit = st.form_submit_button("Send")

if submit and message.strip():
    color = admin_color if st.session_state.username == "aryan" else "white"
    add_message(st.session_state.username, message.strip(), color)
    st.rerun()

st.subheader("\U0001F4DC Chat History")
msgs = get_messages()

if msgs:
    for username, msg, color, ts in msgs:
        time_fmt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        safe_color = color if color else "white"
        msg_color = "white" if username.lower() != "aryan" else safe_color
        st.markdown(f"<span style='color:{safe_color};font-weight:bold'>[{time_fmt}] {username}:</span> <span style='color:{msg_color}'>{msg}</span>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# Auto refresh every 2 seconds using time and rerun
if time.time() % 2 < 0.1:
    time.sleep(0.1)
    st.rerun()
