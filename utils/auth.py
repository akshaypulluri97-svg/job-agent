import os
import streamlit as st
from supabase import create_client

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def get_current_user():
    return st.session_state.get("user")

def handle_token_from_url():
    token = st.query_params.get("access_token")
    if token:
        try:
            supabase = get_supabase()
            refresh  = st.query_params.get("refresh_token", "")
            session  = supabase.auth.set_session(token, refresh)
            st.session_state["user"]    = session.user
            st.session_state["session"] = session
            st.query_params.clear()
            return True
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.query_params.clear()
    return False

def login_screen():
    st.title("💼 Job Applications Agent")
    st.write("Sign in to access your personal job tracker.")

    email = st.text_input("Email address")
    if st.button("Send magic link", type="primary"):
        if not email:
            st.error("Please enter your email address.")
        else:
            try:
                supabase = get_supabase()
                supabase.auth.sign_in_with_otp({"email": email})
                st.success(f"Magic link sent to {email}!")
                st.info("Click the link in your email — you'll be signed in automatically.")
            except Exception as e:
                st.error(f"Could not send link: {e}")

    st.divider()
    with st.expander("Manual token login (if auto-login fails)"):
        st.caption("From the magic link URL copy everything after `access_token=` until `&expires_at`")
        manual_token   = st.text_area("Access token", height=80)
        manual_refresh = st.text_input("Refresh token")
        if st.button("Sign in with token"):
            if not manual_token.strip():
                st.error("Please paste the access token.")
            else:
                try:
                    supabase = get_supabase()
                    session  = supabase.auth.set_session(
                        manual_token.strip(),
                        manual_refresh.strip()
                    )
                    st.session_state["user"]    = session.user
                    st.session_state["session"] = session
                    st.query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

def require_auth():
    if handle_token_from_url():
        st.rerun()
    user = get_current_user()
    if user:
        return user
    login_screen()
    st.stop()
