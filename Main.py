import streamlit as st
import sqlite3
from datetime import datetime
import re
import time

# === DATABASE ===
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# === TABLES ===
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

# === LOGIN & RULES POPUP ===
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

    admin_color = 'gold'  # default admin color

    # Admin text color picker:
    if st.session_state.is_admin:
        admin_color = st.color_picker("Pick your message text color", value=st.session_state.get("admin_color", "#FFD700"), key="color_picker")
        st.session_state.admin_color = admin_color

    if "message_input" not in st.session_state:
        st.session_state.message_input = ""

    message = st.text_input("Your message:", key="message_input", value=st.session_state.message_input)

    send_clicked = st.button("Send", key="send_button")

    if send_clicked and message.strip():
        color = admin_color if st.session_state.is_admin else "black"
        add_message(st.session_state.username, message.strip(), color)
        st.session_state.message_input = ""  # clear input after send
        st.experimental_rerun()

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
        user_to_ban = st.text_input("Ban a username:")
        if st.button("Ban User") and user_to_ban.strip():
            ban_user(user_to_ban.strip())
            st.success(f"✅ {user_to_ban} has been banned.")

        st.write("🧾 Currently Banned Users:")
        banned = get_banned_users()
        st.write(banned if banned else "None")

# === AUTO REFRESH ===
time.sleep(2)
st.experimental_rerun()
