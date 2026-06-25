import os
import streamlit as st
from supabase import create_client

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def get_current_user():
    return st.session_state.get("user")

def login_screen():
    st.title("💼 Job Applications Agent")
    st.write("Sign in to access your personal job tracker.")

    # JavaScript to extract token from URL fragment and pass as query param
    st.components.v1.html("""
        <script>
        const hash = window.location.hash;
        if (hash && hash.includes('access_token')) {
            const params = new URLSearchParams(hash.substring(1));
            const access_token  = params.get('access_token');
            const refresh_token = params.get('refresh_token');
            if (access_token) {
                const url = window.location.pathname +
                    '?access_token=' + encodeURIComponent(access_token) +
                    '&refresh_token=' + encodeURIComponent(refresh_token || '');
                window.location.replace(url);
            }
        }
        </script>
    """, height=0)

    # Handle token passed as query param
    token = st.query_params.get("access_token")
    if token:
        try:
            supabase = get_supabase()
            refresh  = st.query_params.get("refresh_token", "")
            session  = supabase.auth.set_session(token, refresh)
            st.session_state["user"]    = session.user
            st.session_state["session"] = session
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.query_params.clear()
        return

    email = st.text_input("Your email address")
    if st.button("Send magic link", type="primary"):
        if not email:
            st.error("Please enter your email address.")
        else:
            try:
                supabase = get_supabase()
                supabase.auth.sign_in_with_otp({"email": email})
                st.success(f"Check your inbox at {email} — click the link to sign in.")
                st.info("After clicking the link in your email, you'll be signed in automatically.")
            except Exception as e:
                st.error(f"Could not send link: {e}")

def require_auth():
    user = get_current_user()
    if user:
        return user
    login_screen()
    st.stop()
