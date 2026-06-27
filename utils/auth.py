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
            st.error(f"Auto-login failed: {e}")
            st.query_params.clear()
    return False

def login_screen():
    st.title("💼 Job Applications Agent")
    st.write("Sign in to access your personal job tracker.")

    if "otp_email" not in st.session_state:
        st.session_state["otp_email"] = ""
    if "otp_sent" not in st.session_state:
        st.session_state["otp_sent"] = False

    if not st.session_state["otp_sent"]:
        st.subheader("Enter your email")
        email = st.text_input("Email address")
        if st.button("Send OTP code", type="primary"):
            if not email:
                st.error("Please enter your email address.")
            else:
                try:
                    supabase = get_supabase()
                    supabase.auth.sign_in_with_otp({
                        "email": email,
                        "options": {"should_create_user": True}
                    })
                    st.session_state["otp_email"] = email
                    st.session_state["otp_sent"]  = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not send code: {e}")
    else:
        email = st.session_state["otp_email"]
        st.success(f"Code sent to {email}!")
        st.subheader("Enter the 6-digit code from your email")
        otp = st.text_input("6-digit code", max_chars=6, placeholder="123456")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Verify code", type="primary"):
                if not otp.strip():
                    st.error("Please enter the code.")
                else:
                    try:
                        supabase = get_supabase()
                        session  = supabase.auth.verify_otp({
                            "email": email,
                            "token": otp.strip(),
                            "type":  "email",
                        })
                        st.session_state["user"]    = session.user
                        st.session_state["session"] = session
                        st.session_state["otp_sent"]  = False
                        st.session_state["otp_email"] = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"Invalid code: {e}")
        with col2:
            if st.button("Use different email"):
                st.session_state["otp_sent"]  = False
                st.session_state["otp_email"] = ""
                st.rerun()

def require_auth():
    if handle_token_from_url():
        st.rerun()
    user = get_current_user()
    if user:
        return user
    login_screen()
    st.stop()
