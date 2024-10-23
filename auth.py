import hmac
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager


cookies = EncryptedCookieManager(
    prefix="myapp",  
    password=st.secrets["cookies_key"]  
)

if not cookies.ready():
    st.stop()

def check_password():
    """Returns `True` if the user had a correct password."""
    
    def login_form():
        col1, col2, col3 = st.columns([2, 3, 2])
        """Form with widgets to collect user information"""
        with col2:
            with st.form("Credentials"):
                st.text_input("Username", key="username")
                st.text_input("Password", type="password", key="password")
                st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        username = st.session_state["username"]
        password = st.session_state["password"]

        if username in st.secrets["passwords"] and hmac.compare_digest(
            password, st.secrets.passwords[username]
        ):
            st.session_state["password_correct"] = True
            
            cookies["username"] = username
            cookies["logged_in"] = "True"
            cookies.save()
            
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False) or cookies.get("logged_in") == "True":
        return True

    login_form()

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not known or password incorrect")

    return False

# if not check_password():
#     st.stop()

# # Main Streamlit app starts here
# st.write("Here goes your normal Streamlit app...")
# st.button("Click me")
