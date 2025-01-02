import streamlit as st
import pandas as pd
import os
import re

import admin.admin_page as admin_page
import ptr.ptr_page as tester_page
import jira.jira_page as jira_page
import guest.guest_page as guest_page

CSV_FILE = 'user_data.csv'

# Helper functions
def save_to_csv(username, email, password, role='guest'):
    if os.path.exists(CSV_FILE):
        data = pd.DataFrame({
            'Username': [username],
            'Email': [email],
            'Password': [password],
            'Role': [role]
        })
        data.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        data = pd.DataFrame({
            'Username': [username],
            'Email': [email],
            'Password': [password],
            'Role': [role]
        })
        data.to_csv(CSV_FILE, mode='w', header=True, index=False)

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

def is_valid_password(password):
    if len(password) < 6:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    return has_letter and has_number

def validate_user(username, password):
    if os.path.isfile(CSV_FILE):
        data = pd.read_csv(CSV_FILE)
        data['Username'] = data['Username'].astype(str).str.strip()
        data['Password'] = data['Password'].astype(str).str.strip()
        username = username.strip().lower()
        password = password.strip()
        user_record = data[(data['Username'].str.lower() == username) & 
                           (data['Password'] == password)]
        if not user_record.empty:
            return user_record.iloc[0]['Role']
    return None

# email already registered function
def is_email_registered(email):
    if os.path.isfile(CSV_FILE):
        data = pd.read_csv(CSV_FILE)
        return email in data['Email'].values
    return False

# Logout function
def logout():
    for key in ['role', 'username', 'sidebar_state']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Dynamic Navigation
def setup_navigation():
    role = st.session_state.role
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

    admin_1 = st.Page(admin_page.display_admin_page, title="Admin", icon=":material/person:")
    tester_1 = st.Page(tester_page.display_tester_page, title="PTR", icon=":material/conveyor_belt:")
    jira_1 = st.Page(jira_page.display_jira_page, title="JIRA View", icon=":material/visibility:")
    guest_1 = st.Page(guest_page.display_guest_page, title='Guest', icon=':material/location_away:')

    account_pages = [logout_page]

    if role == "admin":
        admin_pages = [admin_1, tester_1, jira_1]
        selected_page = st.navigation({"Admin": admin_pages} | {'Account': account_pages})
        selected_page.run()
    elif role == "user":
        tester_pages = [tester_1, jira_1]
        selected_page = st.navigation({" ": tester_pages} | {'Account': account_pages})
        selected_page.run()
    elif role == "guest":
        guest_pages = [guest_1]
        selected_page = st.navigation({'Guest': guest_pages} | {'Account': account_pages})
        selected_page.run()
    else:
        st.error("Invalid role")

# Main App Logic
# Initialize session state
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"  # Default state
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state, page_title='QA ProjectX', layout='wide')

if st.session_state.role:
    st.session_state.sidebar_state = "expanded"
    setup_navigation()
else:
    st.session_state.sidebar_state = "collapsed"

    # Hide sidebar control when logged out
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            text-align: center;  
            line-height: 1;
            height: 30vh;">
            <div>
                <b style="font-size: 70px; letter-spacing: -0.07em;">Testing Insight</b> <br>
                <b style="color: #ffbd44; font-size: 70px; letter-spacing: -0.07em; margin-left: -20px">Project</b> 
                <b style="color: #ffbd44; font-size: 110px; margin-left: -20px; top: 100px; position: absolute; -webkit-text-stroke: 2px black;">𝒙</b> <br>
            </div>
            <div style="margin-top: 40px; letter-spacing: 0.01em;">
                Designed for <span style="color: #00a29d">Bank Syariah Indonesia (BSI) </span>testing team <br> to simplify test management and enhance decision-making <br>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
                justify-content: center; /* Center align the tabs */
            }

            .stTabs [data-baseweb="tab"] {
                height: 50px;
                padding-left: 125px;
                padding-right: 125px;
            }

        </style>
        """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1,1,1])

        with col1:
            st.header(' ')

        with col2:
            tab1, tab2 = st.tabs(['Login', 'Sign Up'])

            with tab1:
                st.subheader(':wink: Login')
                with st.form(key='login_form'):
                    username = st.text_input('Username')
                    password = st.text_input('Password', type='password')
                    login_button = st.form_submit_button(label='Login')

                if login_button:
                    if username and password:
                        role = validate_user(username, password)
                        if role:
                            # Set session state for the logged-in user
                            st.session_state.role = role
                            st.session_state.username = username
                            st.session_state.sidebar_state = "expanded"
                            st.rerun()  # Refresh to show navigation
                        else:
                            st.error('Invalid username or password')
                    else:
                        st.error('All fields are required')

            with tab2:
                st.subheader(':partying_face: Sign up')
                with st.form(key='signup_form'):
                    username = st.text_input('Username')
                    email = st.text_input('Email')
                    password = st.text_input('Password', type='password')
                    submit_button = st.form_submit_button(label='Sign up')

                    if submit_button:
                        if username and email and password:
                            if is_email_registered(email):
                                st.error('Email already registered. Please use a different email.')
                            elif is_valid_email(email):
                                if is_valid_password(password):
                                    save_to_csv(username, email, password)
                                    st.success("You have successfully signed up! Your role is 'Guest'. Please contact the admin to update your role.\n\n" 
                                            "Nahari Rasif\n" 
                                            "+62 85735536315")
                                else:
                                    st.error('Password must be at least 6 characters long and contain both letters and numbers')
                            else:
                                st.error('Invalid email address. Please enter a valid email')
                        else:
                            st.error('All fields are required')

        with col3:
            st.header(' ')

    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            text-align: center;  
            line-height: 1;
            height: 5vh;">
            <div style="margin-top: 40px;">
                Made with 💛 by 
            <a href="https://www.linkedin.com/in/naharirasif/" target="_blank" style="color: #ffbd44; text-decoration: none;">
                Nahari Rasif
            </a>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
