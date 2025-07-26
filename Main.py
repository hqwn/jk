import streamlit as st
import sqlite3
from datetime import datetime
import re

# === DB ===
DB_FILE = "chat.db"
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

# === BAD WORDS ===
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

# === DB FUNCTIONS ===

def add_message(username, message):
    username = censor_text(username)
    message = censor_text(message)
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

# === AUTH ===
st.title("📡 SQLite Real-time Chat Room")

if "username" not in st.session_state or not st.session_state.username:
    username = st.text_input("Enter your username:")
    if username:
        if username.strip().lower() == "aryan":
            password = st.text_input("Enter admin password:", type="password")
            if password != "monkey@123":
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

# === INTERFACE ===

if st.session_state.is_admin:
    tabs = st.tabs(["Chat", "Admin"])
else:
    tabs = [st]

with tabs[0]:
    message = st.text_input("Your message:")

    if st.button("Send"):
        if message.strip():
            add_message(st.session_state.username, message.strip())
            st.rerun()

    if st.session_state.is_admin:
        if st.button("Clear All Messages"):
            clear_messages()
            st.success("💣 All messages cleared.")
            st.rerun()

    # Simple refresh button
    if st.button("🔄 Refresh Chat"):
        st.rerun()

    st.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.subheader("Chat History (latest first):")
    msgs = get_messages()

    if msgs:
        for username, msg, ts in msgs:
            if username.strip().lower() == "aryan":
                st.markdown(f"<span style='color:gold;font-weight:bold'>[{ts.split('.')[0]}] {username}: {msg}</span>", unsafe_allow_html=True)
            else:
                st.write(f"**[{ts.split('.')[0]}] {username}:** {msg}")
    else:
        st.info("No messages yet.")

# === ADMIN TAB ===

if st.session_state.is_admin:
    with tabs[1]:
        st.subheader("🚨 Admin Tools")

        user_to_ban = st.text_input("Ban a username:")
        if st.button("Ban User") and user_to_ban.strip():
            ban_user(user_to_ban.strip())
            st.success(f"{user_to_ban} has been banned!")

        st.write("Banned users:")
        banned = get_banned_users()
        st.write(banned if banned else "None")
