import streamlit as st
import sqlite3
from datetime import datetime
import re
import time

# === DATABASE SETUP ===
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

# === BAD WORDS FILTER ===
BAD_WORDS = [
    "fuck", "shit", "bitch", "bastard", "asshole", "dick", "cunt",
    "piss", "damn", "slut", "whore", "fag", "faggot", "nigger",
    "nigga", "retard", "spaz", "twat", "cock", "douche", "bollocks",
    "wanker", "arse", "prick", "motherfucker", "goddamn", "bloody",
    "bugger", "pussy", "tit", "boob", "shithead", "dipshit", "cum",
    "suck", "sucker"
]

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

# === DATABASE ACTIONS ===
def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()

def get_messages(limit=50):
    c.execute("SELECT username, message, color, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,))
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

# === UI & LOGIC ===

st.set_page_config(page_title="📡 SQLite Real-time Chat Room", layout="wide")
st.title("📡 SQLite Real-time Chat Room")

# Login and rules popup - only once per session
if "username" not in st.session_state or not st.session_state.username:
    username = st.text_input("Enter your username:")
    if username:
        if "rules_accepted" not in st.session_state:
            st.info(
                """
                **Welcome to the chat! Please follow these rules:**

                1. No offensive language.
                2. No spamming.
                3. Admin username: aryan (password protected)
                4. Misconduct leads to ban.

                By continuing, you accept these rules.
                """
            )
            accept = st.button("I Accept the Rules")
            if not accept:
                st.stop()
            st.session_state.rules_accepted = True

        if username.strip().lower() == "aryan":
            password = st.text_input("Enter admin password:", type="password")
            if password != "patrick@234":
                st.warning("🔒 Wrong password. Try again.")
                st.stop()
            else:
                st.session_state.is_admin = True
        else:
            st.session_state.is_admin = False
        st.session_state.username = username.strip()
    else:
        st.stop()

if is_banned(st.session_state.username):
    st.error("🚫 You are banned from this chat.")
    st.stop()

# Tabs
if st.session_state.is_admin:
    tabs = st.tabs(["💬 Chat", "🛠️ Admin"])
    chat_tab, admin_tab = tabs
else:
    tabs = st.tabs(["💬 Chat"])
    chat_tab = tabs[0]

with chat_tab:
    st.subheader("Send Message")

    # Admin color picker
    if st.session_state.is_admin:
        admin_color = st.color_picker(
            "Pick your message text color",
            value=st.session_state.get("admin_color", "#FFD700"),
            key="color_picker"
        )
        st.session_state.admin_color = admin_color
    else:
        admin_color = None

    # Initialize message input in session_state if not exists
    if "message_input" not in st.session_state:
        st.session_state.message_input = ""

    # Text input without on_change
    message = st.text_input("Your message:", key="message_input")

    if st.button("Send"):
        msg = st.session_state.message_input.strip()
        if msg:
            color = st.session_state.admin_color if st.session_state.is_admin else "white"
            add_message(st.session_state.username, msg, color)
            st.session_state.message_input = ""  # clear input after send
            st.experimental_rerun()  # rerun after sending

    # Admin clear messages button
    if st.session_state.is_admin:
        if st.button("🧨 Clear All Messages"):
            clear_messages()
            st.success("💣 All messages cleared.")
            st.experimental_rerun()

    st.subheader("📜 Chat History (latest first)")

    messages = get_messages()

    if messages:
        for username, msg, color, ts in messages:
            if username.strip().lower() == "aryan":
                used_color = color if color else "#FFD700"
                st.markdown(
                    f"<span style='color:{used_color};font-weight:bold'>[{ts.split('.')[0]}] {username}: {msg}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<span style='color:white'>[{ts.split('.')[0]}] {username}:</span> {msg}",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No messages yet.")


    # Admin clear messages button
    if st.session_state.is_admin:
        if st.button("🧨 Clear All Messages"):
            clear_messages()
            st.success("💣 All messages cleared.")
            st.rerun()

    st.subheader("📜 Chat History (latest first)")

    messages = get_messages()

    if messages:
        for username, msg, color, ts in messages:
            if username.strip().lower() == "aryan":
                used_color = color if color else "#FFD700"
                st.markdown(
                    f"<span style='color:{used_color};font-weight:bold'>[{ts.split('.')[0]}] {username}: {msg}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<span style='color:white'>[{ts.split('.')[0]}] {username}:</span> {msg}",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No messages yet.")

if st.session_state.is_admin:
    with admin_tab:
        st.subheader("🚨 Admin Tools")
        user_to_ban = st.text_input("Ban a username:")
        if st.button("Ban User") and user_to_ban.strip():
            ban_user(user_to_ban.strip())
            st.success(f"✅ {user_to_ban} has been banned.")

        st.write("🧾 Currently Banned Users:")
        banned = get_banned_users()
        st.write(banned if banned else "None")

# Auto-refresh every 2 seconds
time.sleep(2)
st.rerun()
