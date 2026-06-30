import os
import streamlit as st
from supabase import create_client

def get_supabase():
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
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
                supabase.auth.sign_in_with_otp({
                    "email": email,
                    "options": {"should_create_user": True}
                })
                st.success(f"Magic link sent to {email}!")
                st.info("Check your inbox and click the link to sign in automatically.")
            except Exception as e:
                st.error(f"Could not send link: {e}")

def require_auth():
    # ── Local dev bypass ─────────────────────────────────────────
    if os.getenv("LOCAL_DEV") == "true":
        if "user" not in st.session_state:
            class _FakeUser:
                id    = "00000000-0000-0000-0000-000000000001"
                email = "dev@localhost"
            st.session_state["user"] = _FakeUser()
        return st.session_state["user"]
    # ─────────────────────────────────────────────────────────────
    if handle_token_from_url():
        st.rerun()
    user = get_current_user()
    if user:
        return user
    login_screen()
    st.stop()


