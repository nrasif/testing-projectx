import streamlit as st
import pandas as pd
import os

CSV_FILE = 'user_data.csv'

def display_admin_page():
    st.title(":orange[Manage Users]")

    # Check if the CSV file exists
    if os.path.exists(CSV_FILE):
        # Load user data from the CSV file
        data = pd.read_csv(CSV_FILE)
        st.write("Edit user roles in the table below and click 'Save changes'.")

        edited_data = st.data_editor(data, use_container_width=True, num_rows="dynamic")

        # Save changes to the CSV when the admin clicks 'Save changes'
        if st.button('Save changes'):
            # Validate if Role is in the correct format (optional)
            valid_roles = ['admin', 'tester', 'viewer', 'guest']
            if all(role in valid_roles for role in edited_data['Role']):
                edited_data.to_csv(CSV_FILE, index=False)
                st.success('User data updated successfully!')
            else:
                st.error('Invalid role found! Roles must be one of the following: admin, tester, viewer')
    else:
        st.error("No user data found. Please ensure the user_data.csv file exists.")

