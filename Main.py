import streamlit as st
import sqlite3
import re
import time
from datetime import datetime
import pandas as pd

# --- DB setup ---
DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create messages and ban tables
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

# --- Censorship ---
BAD_WORDS = [
    # Basic profanity
    "fuck", "shit", "bitch", "asshole", "bastard", "dick", "cock", "pussy", "cunt", "tit", "whore", "slut",

    # Variants and leetspeak
    "fck", "fuk", "f*ck", "f**k", "sh1t", "sht", "biatch", "b!tch", "a$$", "d1ck", "p*ssy", "c0ck", "w*ore", "s1ut",

    # Racial/ethnic slurs (use with caution; important for moderation)
    "nigger", "nigga", "chink", "spic", "gook", "kike", "raghead", "camel jockey",

    # Homophobic/transphobic slurs
    "fag", "faggot", "dyke", "tranny", "homo", "queer",

    # Self-harm or violent phrases (optional)
    "kill myself", "commit suicide", "die bitch",

    # Sexual harassment terms
    "suck my dick", "blowjob", "handjob", "anal", "deepthroat", "69", "cum", "jizz", "masturbate", "fingering",

    # Insults/slurs (general)
    "retard", "moron", "idiot", "dumbass", "loser"
]


def build_obfuscated_pattern(word):
    return ''.join([re.escape(ch) + r'\s*[^a-zA-Z0-9]*' for ch in word])

def censor_text(text):
    for word in BAD_WORDS:
        pattern = build_obfuscated_pattern(word)
        text = re.sub(pattern, lambda m: '*' * len(word), text, flags=re.IGNORECASE)
    return text

# --- Core Functions ---
def add_message(username, message, color='white'):
    username = censor_text(username)
    message = censor_text(message)
    c.execute("INSERT INTO messages (username, message, color) VALUES (?, ?, ?)", (username, message, color))
    conn.commit()
    delete_old_messages()

def get_messages(limit=100):
    c.execute("SELECT id, username, message, color FROM messages ORDER BY id ASC LIMIT ?", (limit,))
    return c.fetchall()

def delete_old_messages():
    c.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT 100)")
    conn.commit()

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

# --- Streamlit Config ---
st.set_page_config(page_title="💬 Chat Room", layout="wide")
st.markdown(
    """
    <style>
        .block-container {padding-top: 1rem;}
        [data-testid="stChatInput"] {position: fixed; bottom: 1rem; width: 100%;}
        [data-testid="stVerticalBlock"] > div {padding-bottom: 3rem;}
        .chat-bubble {
            padding: 0.75rem 1rem;
            border-radius: 1rem;
            margin-bottom: 0.4rem;
            max-width: 70%;
            color: white;
            font-size: 0.95rem;
            word-break: break-word;
        }
        .mine { background-color: #1e90ff; align-self: flex-end; }
        .theirs { background-color: #2f3136; align-self: flex-start; }
        .username-label {
            font-size: 0.75rem;
            color: #aaa;
            margin-bottom: 0.1rem;
            margin-left: 0.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session Setup ---
if "username" not in st.session_state:
    with st.container():
        st.title("🧾 Enter Chat Room")
        username = st.text_input("Pick a username:")
        if username:
            if username.lower() == "aryan":
                password = st.text_input("Enter admin password", type="password")
                if password != "thisisnotmypassword":
                    st.warning("Wrong password for admin.")
                    st.stop()
                else:
                    st.success("Welcome back Aryan")
                    st.session_state.username = "aryan"
                    st.session_state.is_admin = True
                    st.rerun()
            else:
                if is_banned(username):
                    st.error("You're banned from this chat.")
                    st.stop()
                st.session_state.username = username.strip()
                st.session_state.is_admin = False
                st.rerun()
    st.stop()

# --- Admin Panel ---
if st.session_state.username == "aryan":
    with st.sidebar:
        st.title("🛠 Admin Panel")

        ban_target = st.text_input("Ban user")
        if st.button("🚫 Ban") and ban_target:
            ban_user(ban_target)
            st.success(f"Banned {ban_target}")

        unban_target = st.text_input("Unban user")
        if st.button("✅ Unban") and unban_target:
            unban_user(unban_target)
            st.success(f"Unbanned {unban_target}")

        msg_id = st.text_input("Delete message ID")
        if st.button("🧹 Delete Msg") and msg_id.isdigit():
            delete_message_by_id(int(msg_id))
            st.success(f"Deleted message ID {msg_id}")

        if st.button("🗑 Clear Chat"):
            clear_chat()
            st.success("Chat cleared")

        if st.button("📥 Export CSV"):
            c.execute("SELECT * FROM messages ORDER BY id")
            df = pd.DataFrame(c.fetchall(), columns=["ID", "Username", "Message", "Color", "Timestamp"])
            st.download_button("Download chat_history.csv", df.to_csv(index=False), file_name="chat_history.csv")

# --- Chat UI ---
st.title("💬 Real-time Chat")
messages = get_messages()

# Chat bubbles
for _, uname, msg, color in messages:
    is_me = uname == st.session_state.username
    bubble_class = "mine" if is_me else "theirs"
    with st.chat_message(uname if uname != "aryan" else "Admin", avatar="👤" if uname != "aryan" else "🛠"):
        st.markdown(f"<div class='username-label'>{uname}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble {bubble_class}' style='background-color:{color if uname=='aryan' else '#2f3136'}'>{msg}</div>", unsafe_allow_html=True)

# --- Message Input (Sticky at Bottom) ---
msg_color = st.color_picker("Pick your color", "#1e90ff") if st.session_state.username == "aryan" else "#2f3136"
message = st.chat_input("Type your message...")

if message:
    add_message(st.session_state.username, message.strip(), msg_color)
    st.rerun()
time.sleep(2)
st.rerun()
