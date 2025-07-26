import streamlit as st
import sqlite3
import re
import time
from datetime import datetime

# DB setup (same as before)
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

# Bad words & censor functions (same as before) ...
BAD_WORDS = ["fuck", "shit", "bitch", "asshole", "dick"]  # trimmed for brevity

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

def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()

def get_messages(limit=50):
    c.execute("SELECT username, message, color, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return c.fetchall()

# Simplified auth for demo
if "username" not in st.session_state:
    username = st.text_input("Enter your username:")
    if username:
        st.session_state.username = username.strip()
    else:
        st.stop()

# Main chat UI
st.title("📡 SQLite Real-time Chat Room")

if "admin_color" not in st.session_state:
    st.session_state.admin_color = "#FFD700"  # gold default

admin_color = st.color_picker("Pick admin message color", st.session_state.admin_color) if st.session_state.username.lower() == "aryan" else None
if admin_color:
    st.session_state.admin_color = admin_color

with st.form(key="message_form", clear_on_submit=True):
    message = st.text_input("Your message:")
    submit = st.form_submit_button("Send")

if submit and message.strip():
    color = st.session_state.admin_color if st.session_state.username.lower() == "aryan" else "white"
    add_message(st.session_state.username, message.strip(), color)
    st.experimental_rerun()

st.subheader("📜 Chat History (latest first)")
msgs = get_messages()

if msgs:
    for username, msg, color, ts in msgs:
        display_time = ts.split(".")[0]
        safe_color = color if color else "white"
        st.markdown(f"<span style='color:{safe_color};font-weight:bold'>[{display_time}] {username}:</span> <span style='color:white'>{msg}</span>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

time.sleep(2)
st.experimental_rerun()
