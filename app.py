import streamlit as st
from utils.ai_ranking import dashboard_main

# Simulated user database (replace with real DB in production)
USER_DB = [
    "admin@gmail.com"
]

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "login"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #4CAF50;  /* Green background */
        color: white;              /* White text */
        font-size: 16px;           /* Font size */
    }
    div.stButton > button:hover {
        background-color: #45a049; /* Darker green on hover */
    }
    div.stButton > text_input:first-child {
       width: 400px;   
    }
    </style>
""", unsafe_allow_html=True)

def login():
    st.title("🔑 Login Page")

    email = st.text_input("email")

    if st.button("Login"):
        if email in USER_DB:
            st.session_state.authenticated = True
            st.session_state.email = email
            st.session_state.page = "dashboard_main"
            st.rerun()
        else:
            st.error("Invalid user email")

    st.write("Don't have an account?")
    if st.button("Go to Signup"):
        st.session_state.page = "signup"
        st.rerun()


def signup():
    st.title("📝 Signup Page")

    new_user = st.text_input("Enter your email")

    if st.button("Signup"):
        if new_user in USER_DB:
            st.error("Username already exists!")
        elif len(new_user.strip()) == 0:
            st.error("Fields cannot be empty!")
        else:
            USER_DB.append(new_user)
            st.success("Account created successfully! Please log in.")
            st.session_state.page = "login"
            st.rerun()

    st.write("Already have an account?")
    if st.button("Go to Login"):
        st.session_state.page = "login"
        st.rerun()


def main():
    if st.session_state.authenticated:
        st.title(f"🎉 Welcome! **{st.session_state.email}**")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.page = "login"
            st.rerun()
        if st.session_state.page == "dashboard_main":
            dashboard_main()

    else:
        if st.session_state.page == "login":
            login()
        elif st.session_state.page == "signup":
            signup()


if __name__ == "__main__":
    main()
