import streamlit as st
from Components.gdrive_database.gdrive_conn import googleConnect
from Components.gdrive_database.googledrive_ID import SCOPE_ID, SERVICE_ACC_ID, PARENT_FOLDER

# Configuration
SERVICE_ACCOUNT_FILE = SERVICE_ACC_ID
SCOPES = SCOPE_ID
PARENT_FOLDER_ID = PARENT_FOLDER

# Instantiate the GoogleDriveAPI class
drive_api = googleConnect(SERVICE_ACCOUNT_FILE, SCOPES, PARENT_FOLDER_ID)

# Get a list of files
files = drive_api.get_list_files()
st.write("Files in Google Drive:", files)

