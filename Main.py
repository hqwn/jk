# === INTERFACE ===

if st.session_state.is_admin:
    tabs = st.tabs(["Chat", "Admin"])
    chat_tab, admin_tab = tabs
else:
    tabs = st.tabs(["Chat"])
    chat_tab = tabs[0]

with chat_tab:
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

if st.session_state.is_admin:
    with admin_tab:
        st.subheader("🚨 Admin Tools")

        user_to_ban = st.text_input("Ban a username:")
        if st.button("Ban User") and user_to_ban.strip():
            ban_user(user_to_ban.strip())
            st.success(f"{user_to_ban} has been banned!")

        st.write("Banned users:")
        banned = get_banned_users()
        st.write(banned if banned else "None")
