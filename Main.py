import streamlit as st
import sqlite3
import re
import time
from datetime import datetime
import pandas as pd

# --- Database setup ---
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
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

# --- Censorship logic ---
BAD_WORDS = ["fuck", "shit", "bitch", "asshole", "dick"]

def build_obfuscated_pattern(word):
    return ''.join([re.escape(ch) + r'\s*[^a-zA-Z0-9]*' for ch in word])

def censor_text(text):
    for word in BAD_WORDS:
        pattern = build_obfuscated_pattern(word)
        text = re.sub(pattern, lambda m: '*' * len(word), text, flags=re.IGNORECASE)
    return text

# --- Message Functions ---
def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()
    delete_old_messages()

def get_messages(limit=50):
    c.execute("SELECT id, username, message, color, timestamp FROM messages ORDER BY id ASC LIMIT ?", (limit,))
    return c.fetchall()

def delete_old_messages():
    c.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 50)")
    conn.commit()

# --- Admin & User Management ---
def is_banned(username):
    c.execute("SELECT 1 FROM banned_users WHERE username=?", (username,))
    return c.fetchone() is not None

def ban_user(username):
    c.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    conn.commit()

def unban_user(username):
    c.execute("DELETE FROM banned_users WHERE username=?", (username,))
    conn.commit()

def delete_message_by_id(msg_id):
    c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()

def clear_chat():
    c.execute("DELETE FROM messages")
    conn.commit()

# --- Session State Setup ---
st.set_page_config(page_title="💬 Discord-style Chat", page_icon="💬", layout="wide")

if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "slow_mode" not in st.session_state:
    st.session_state.slow_mode = False

# --- Login Logic ---
if not st.session_state.username:
    with st.sidebar:
        st.title("🔐 Login")
        username = st.text_input("Username:")
        if username:
            if username.lower() == "aryan":
                pwd = st.text_input("Admin Password", type="password")
                if pwd == "thisisnotmypassword":
                    st.session_state.admin_authenticated = True
                    st.session_state.username = "aryan"
                else:
                    st.warning("Wrong password")
                    st.stop()
            else:
                if is_banned(username.strip()):
                    st.error("🚫 You are banned from this chat.")
                    st.stop()
                st.session_state.username = username.strip()
    st.stop()

# --- Admin Panel ---
if st.session_state.username == "aryan" and st.session_state.admin_authenticated:
    with st.sidebar:
        st.title("🔧 Admin Panel")

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

        if st.button("📥 Download Chat"):
            c.execute("SELECT * FROM messages ORDER BY id")
            df = pd.DataFrame(c.fetchall(), columns=["ID", "Username", "Message", "Color", "Timestamp"])
            st.download_button("Download CSV", df.to_csv(index=False), file_name="chat_history.csv")

# --- Display Chat Messages ---
st.markdown("<style>div.block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)
st.title("💬 Live Chat")

with st.container():
    messages = get_messages()
    for mid, username, text, color, ts in messages:
        ts_fmt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        with st.chat_message(username if username != "aryan" else "Admin", avatar="👤" if username != "aryan" else "🛠"):
            st.markdown(f"**[{ts_fmt}] {username}**", unsafe_allow_html=True)
            st.markdown(f"<div style='color:{color}'>{text}</div>", unsafe_allow_html=True)

# --- Chat Input (Bottom) ---
with st.container():
    st.markdown("---")
    if st.session_state.username == "aryan":
        admin_color = st.color_picker("Pick admin message color", "#FFD700")
    else:
        admin_color = "white"

    msg = st.chat_input("Type your message...")
    if msg:
        add_message(st.session_state.username, msg.strip(), admin_color)
        if st.session_state.slow_mode:
            time.sleep(3)
        st.rerun()
