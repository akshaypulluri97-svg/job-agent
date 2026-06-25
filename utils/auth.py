import os
import streamlit as st
from supabase import create_client

def get_supabase():
    """Get Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def get_current_user():
    """Return user from session_state or None."""
    return st.session_state.get("user")

def login_screen():
    """Render magic link login UI."""
    st.title("💼 Job Applications Agent")
    st.write("Sign in to access your personal job tracker.")

    email = st.text_input("Your email address")

    if st.button("Send magic link", type="primary"):
        if not email:
            st.error("Please enter your email address.")
        else:
            try:
                supabase = get_supabase()
                supabase.auth.sign_in_with_otp({"email": email})
                st.success(f"Check your inbox at {email} — click the link to sign in.")
                st.info("After clicking the link, come back here and refresh the page.")
            except Exception as e:
                st.error(f"Could not send link: {e}")

    token = st.query_params.get("access_token")
    if token:
        try:
            supabase = get_supabase()
            refresh = st.query_params.get("refresh_token", "")
            session = supabase.auth.set_session(token, refresh)
            st.session_state["user"]    = session.user
            st.session_state["session"] = session
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def require_auth():
    """Call at top of app.py. Returns user if authenticated, else shows login and stops."""
    user = get_current_user()
    if user:
        return user
    login_screen()
    st.stop()
