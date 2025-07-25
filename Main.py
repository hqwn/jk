

import streamlit as st
import time
import os
MAX_LINES = 20
CHAT_FILE = "chat.txt"
BAD_WORDS = [
    "fuck",
    "shit",
    "bitch",
    "bastard",
    "asshole",
    "dick",
    "cunt",
    "piss",
    "damn",
    "slut",
    "whore",
    "fag",
    "faggot",
    "nigger",
    "nigga",
    "retard",
    "spaz",
    "twat",
    "cock",
    "douche",
    "bollocks",
    "wanker",
    "arse",
    "prick",
    "motherfucker",
    "goddamn",
    "bloody",
    "bugger",
    "pussy",
    "tit",
    "boob",
    "shithead",
    "dipshit",
    "cum",
    "suck",
    "sucker",
]

# Function to read chat
def read_chat():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            messages = f.readlines()
        return messages
    else:
        return []


import re

def censor_message(message, bad_words):
    pattern = re.compile(
        r'\b(' + '|'.join(re.escape(word) for word in bad_words) + r')\b',
        flags=re.IGNORECASE
    )
    return pattern.sub(lambda m: '*' * len(m.group()), message)



# Function to write message
def write_message(username, message):
    message = censor_message(message, BAD_WORDS)
    # Append new message
    with open(CHAT_FILE, "a") as f:
        f.write(f"{username}: {message}\n")
    
    # Read all messages after appending
    messages = read_chat()

    # If more than MAX_LINES, keep only the newest MAX_LINES
    if len(messages) > MAX_LINES:
        messages = messages[-MAX_LINES:]
        with open(CHAT_FILE, "w") as f:
            with open(CHAT_FILE, "w") as f:
                pass  # This clears the file completely


# Streamlit App
st.title("📡 Real-time CHat romom")

# Get username
b =  st.text_input("Enter your name to join:", key="username_input")

# Message input
message = st.text_input("Your message:", key="message_input")

# Send button
if st.button("Send"):
    if not b:
        b = 'anonymous'
    if message.strip() != "":
        if message.strip() == 'clear sesame':
            with open(CHAT_FILE, "w") as f:
                pass  # This clears the file completely
        else:
            write_message(b, message)
            st.rerun()
# Show chat history
st.subheader("Chat History:")

# Auto-refresh every few seconds
messages = read_chat()

for msg in reversed(messages):
    st.write(msg.strip())

# Optional: auto-refresh every few seconds
time.sleep(2)
st.rerun()
