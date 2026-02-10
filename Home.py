import streamlit as st
from services.database import init_database
from services.auth_service import authenticate_user

# Initialize database on first run
init_database()

st.set_page_config(
    page_title="Call Center Panel",
    page_icon="📞",
    layout="wide"
)

# Check if already logged in
if 'user' in st.session_state:
    user = st.session_state.user
    if user['role'] == 'admin':
        st.switch_page("pages/1_Admin_Panel.py")
    else:
        st.switch_page("pages/2_Operator_Panel.py")

st.title("📞 Call Center Panel")
st.subheader("Giriş Yap")

with st.form("login_form"):
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    submit = st.form_submit_button("Giriş")

    if submit:
        user = authenticate_user(username, password)

        if user:
            st.session_state.user = user
            st.success(f"Hoş geldiniz, {user['full_name']}!")

            # Redirect based on role
            if user['role'] == 'admin':
                st.switch_page("pages/1_Admin_Panel.py")
            else:
                st.switch_page("pages/2_Operator_Panel.py")
        else:
            st.error("Kullanıcı adı veya şifre hatalı!")

st.info("**Test Kullanıcısı:** admin / admin123")
