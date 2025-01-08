# qa_projectx_app.py

import streamlit as st
import pandas as pd
import os
import re

# how to use this in app.py
# from Components.login_page import loginPage

# app = loginPage(csv_file='user_data.csv')
#app.run()



class loginPage:
    
    # THIS IS THE AREA OF HOW LOGIN LOGOUT USING CSV FILE WORK
    
    def __init__(self, csv_file='user_data.csv'):
        self.csv_file = csv_file
        self.initialize_session_state()

    def initialize_session_state(self):
        if 'is_logged_in' not in st.session_state:
            st.session_state['is_logged_in'] = False
        if 'role' not in st.session_state:
            st.session_state['role'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'active_page' not in st.session_state:
            st.session_state['active_page'] = None

    def save_to_csv(self, username, email, password, role='guest'):
        data = pd.DataFrame({
            'Username': [username],
            'Email': [email],
            'Password': [password],
            'Role': [role]
        })
        if os.path.exists(self.csv_file):
            data.to_csv(self.csv_file, mode='a', header=False, index=False)
        else:
            data.to_csv(self.csv_file, mode='w', header=True, index=False)

    @staticmethod
    def is_valid_email(email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None

    @staticmethod
    def is_valid_password(password):
        if len(password) < 6:
            return False
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        return has_letter and has_number

    def validate_user(self, username, password):
        if os.path.isfile(self.csv_file):
            data = pd.read_csv(self.csv_file)
            data['Username'] = data['Username'].astype(str).str.strip()
            data['Password'] = data['Password'].astype(str).str.strip()
            username = username.strip().lower()
            password = password.strip()
            user_record = data[(data['Username'].str.lower() == username) & \
                               (data['Password'] == password)]
            if not user_record.empty:
                return user_record.iloc[0]['Role']
        return None

    def is_email_registered(self, email):
        if os.path.isfile(self.csv_file):
            data = pd.read_csv(self.csv_file)
            return email in data['Email'].values
        return False

    # Rerun the page after logout in order to clear the cookies
    def logout(self):
        st.session_state.clear()
        st.session_state['is_logged_in'] = False
        st.session_state['role'] = None
        st.session_state['username'] = None
        st.rerun()

    def login(self, username, password):
        role = self.validate_user(username, password)
        if role:
            st.session_state['is_logged_in'] = True
            st.session_state['role'] = role
            st.session_state['username'] = username
            st.session_state['active_page'] = None
            st.rerun()
        else:
            st.error('Invalid username or password')

    def run(self):
        # Defining the page title and the layout
        st.set_page_config(page_title='QA ProjectX', layout='wide')

        if st.session_state['is_logged_in']:
            self.display_logged_in_view()
        else:
            self.display_logged_out_view()
            
    # -------------------------------------------------------------

    def display_logged_in_view(self):
        st.sidebar.markdown(f"""
            <div style="margin-bottom: 20px;">
            <b style="font-size: 20px;">Welcome, <span style="color: #ffbd44;">{st.session_state['username']}!</span></b>
            </div>
        """, unsafe_allow_html=True)

        role = st.session_state['role']
        pages = self.get_pages_by_role(role)

        selected_page = st.sidebar.selectbox("Menu", pages)

        if selected_page == "Logout":
            self.logout()
        else:
            self.handle_page_selection(selected_page)

    def display_logged_out_view(self):
        tab1, tab2 = st.tabs(['Login', 'Sign Up'])

        with tab1:
            self.display_login_form()

        with tab2:
            self.display_signup_form()

    def display_login_form(self):
        st.subheader('Login')
        with st.form(key='login_form'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            login_button = st.form_submit_button(label='Login')

            if login_button:
                if username and password:
                    self.login(username, password)
                else:
                    st.error('All fields are required')

    def display_signup_form(self):
        st.subheader('Sign Up')
        with st.form(key='signup_form'):
            username = st.text_input('Username')
            email = st.text_input('Email')
            password = st.text_input('Password', type='password')
            submit_button = st.form_submit_button(label='Sign up')

            if submit_button:
                if username and email and password:
                    if self.is_email_registered(email):
                        st.error('Email already registered. Please use a different email.')
                    elif self.is_valid_email(email):
                        if self.is_valid_password(password):
                            self.save_to_csv(username, email, password)
                            st.success("You have successfully signed up! Your role is 'Guest'. Please contact the admin to update your role.")
                        else:
                            st.error('Password must be at least 6 characters long and contain both letters and numbers')
                    else:
                        st.error('Invalid email address. Please enter a valid email')
                else:
                    st.error('All fields are required')
                    
    # get page based on role you loggged in
    def get_pages_by_role(self, role):
        if role == 'admin':
            return ["Admin Page", "PTR Page", "JIRA Page", "Logout"]
        elif role == 'user':
            return ["PTR Page", "JIRA Page", "Logout"]
        elif role == 'guest':
            return ["Guest Page", "Logout"]
        return []

    #importing page by role (need to define which page you want to go in)
    def handle_page_selection(self, page):
        if page == "Admin Page":
            import admin.admin_page as admin_page
            admin_page.display_admin_page()
        elif page == "PTR Page":
            import ptr.ptr_page as tester_page
            tester_page.display_tester_page()
        elif page == "JIRA Page":
            import jira.jira_page as jira_page
            jira_page.display_jira_page()
        elif page == "Guest Page":
            import guest.guest_page as guest_page
            guest_page.display_guest_page()

# Usage
if __name__ == "__main__":
    app = loginPage()
    app.run()
