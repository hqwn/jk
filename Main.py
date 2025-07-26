import streamlit as st
import sqlite3
from datetime import datetime
import re
import time
import pandas as pd
import io

# === DATABASE SETUP ===
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        color TEXT DEFAULT 'black',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS banned_users (
        username TEXT PRIMARY KEY
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS muted_users (
        username TEXT PRIMARY KEY
    )
""")
try:
    c.execute('ALTER TABLE messages ADD COLUMN color TEXT DEFAULT \'black\';')
except:
    pass
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

# === DB ACTIONS ===
def add_message(username, message, color='black'):
    username = censor_text(username)
    message = censor_text(message)
    # Don't add message if user is muted
    if is_muted(username):
        return
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
    # Also unmute banned user
    unmute_user(username)
    conn.commit()

def is_banned(username):
    c.execute("SELECT 1 FROM banned_users WHERE username = ?", (username,))
    return c.fetchone() is not None

def get_banned_users():
    c.execute("SELECT username FROM banned_users")
    return [row[0] for row in c.fetchall()]

def mute_user(username):
    c.execute("INSERT OR IGNORE INTO muted_users (username) VALUES (?)", (username,))
    conn.commit()

def unmute_user(username):
    c.execute("DELETE FROM muted_users WHERE username = ?", (username,))
    conn.commit()

def is_muted(username):
    c.execute("SELECT 1 FROM muted_users WHERE username = ?", (username,))
    return c.fetchone() is not None

def get_muted_users():
    c.execute("SELECT username FROM muted_users")
    return [row[0] for row in c.fetchall()]

def get_stats():
    c.execute("SELECT COUNT(DISTINCT username) FROM messages")
    users_count = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM messages")
    messages_count = c.fetchone()[0] or 0
    return users_count, messages_count

def export_chat():
    c.execute("SELECT username, message, color, timestamp FROM messages ORDER BY id")
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["Username", "Message", "Color", "Timestamp"])
    return df.to_csv(index=False).encode('utf-8')

# === APP START ===
st.set_page_config("Chat Room", layout="wide")
st.title("📡 SQLite Real-time Chat Room")

if "username" not in st.session_state or not st.session_state.username:
    username = st.text_input("Enter your username:", key="username_input")
    if username:
        if "rules_accepted" not in st.session_state:
            st.info("""
            **Welcome to the chat! Please follow these rules:**

            1. No offensive language.
            2. No spamming.
            3. Admin Username: aryan, if you guess the password you can be admin with me
            4. I can ban you forever if you do something bad

            By continuing, you accept these rules.
            """)
            accept = st.button("I Accept the Rules", key="accept_rules")
            if not accept:
                st.stop()
            st.session_state.rules_accepted = True

        if username.strip().lower() == "aryan":
            password = st.text_input("Enter admin password:", type="password", key="admin_password")
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

# === TABS ===
if st.session_state.is_admin:
    tabs = st.tabs(["💬 Chat", "🛠️ Admin"])
    chat_tab, admin_tab = tabs
else:
    tabs = st.tabs(["💬 Chat"])
    chat_tab = tabs[0]

# === CHAT TAB ===
with chat_tab:
    st.subheader("Send Message")

    admin_color = 'gold'
    if st.session_state.is_admin:
        admin_color = st.color_picker("Pick your message text color", value=st.session_state.get("admin_color", "#FFD700"), key="color_picker")
        st.session_state.admin_color = admin_color

    if "message_input" not in st.session_state:
        st.session_state.message_input = ""

    send_clicked = st.button("Send", key="send_button")

    if send_clicked and st.session_state.message_input.strip():
        add_message(st.session_state.username, st.session_state.message_input.strip(), admin_color if st.session_state.is_admin else "black")
        st.session_state.message_input = ""
        st.rerun()

    message = st.text_input("Your message:", key="message_input", value=st.session_state.message_input)

    st.subheader("📜 Chat History (latest first)")

    msgs = get_messages()

    if msgs:
        for username, msg, color, ts in msgs:
            display_name = f"**[{ts.split('.')[0]}] {username}:**"
            if username.strip().lower() == "aryan":
                used_color = color if color else "gold"
                st.markdown(f"<span style='color:{used_color};font-weight:bold'>[{ts.split('.')[0]}] {username}: {msg}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:black'>{display_name} {msg}</span>", unsafe_allow_html=True)
    else:
        st.info("No messages yet.")

# === ADMIN TAB ===
if st.session_state.is_admin:
    with admin_tab:
        st.subheader("🚨 Admin Tools")

        # Ban User
        user_to_ban = st.text_input("Ban a username:", key="ban_user")
        if st.button("Ban User") and user_to_ban.strip():
            ban_user(user_to_ban.strip())
            st.success(f"✅ {user_to_ban} has been banned.")

        # Mute User
        user_to_mute = st.text_input("Mute a username:", key="mute_user")
        if st.button("Mute User") and user_to_mute.strip():
            mute_user(user_to_mute.strip())
            st.success(f"🔇 {user_to_mute} has been muted.")

        # Unmute User
        user_to_unmute = st.text_input("Unmute a username:", key="unmute_user")
        if st.button("Unmute User") and user_to_unmute.strip():
            unmute_user(user_to_unmute.strip())
            st.success(f"🔊 {user_to_unmute} has been unmuted.")

        # Clear all messages
        if st.button("🧨 Clear All Messages"):
            clear_messages()
            st.success("💣 All messages cleared.")

        # Export chat CSV
        if st.button("📤 Export Chat History as CSV"):
            csv_data = export_chat()
            st.download_button("Download Chat CSV", csv_data, file_name="chat_history.csv", mime="text/csv")

        # Show banned users
        st.write("🧾 Currently Banned Users:")
        banned = get_banned_users()
        st.write(banned if banned else "None")

        # Show muted users
        st.write("🔇 Currently Muted Users:")
        muted = get_muted_users()
        st.write(muted if muted else "None")

        # Stats
        users_count, messages_count = get_stats()
        st.write(f"📊 Total users who messaged: **{users_count}**")
        st.write(f"💬 Total messages sent: **{messages_count}**")

# === AUTO REFRESH ===
time.sleep(2)
st.rerun()
