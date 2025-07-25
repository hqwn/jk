

import streamlit as st
import time
import os
MAX_LINES = 20
CHAT_FILE = "chat.txt"

# Function to read chat
def read_chat():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            messages = f.readlines()
        return messages
    else:
        return []

# Function to write message
def write_message(username, message):
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
if "username" not in st.session_state:
    st.session_state.username = st.text_input("Enter your name to join:", key="username_input")
    st.stop()

# Message input
message = st.text_input("Your message:", key="message_input")

# Send button
if st.button("Send"):
    if message.strip() != "":
        if message.strip() == 'clear sesame':
            with open(CHAT_FILE, "w") as f:
                pass  # This clears the file completely
        write_message(st.session_state.username, message)
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
