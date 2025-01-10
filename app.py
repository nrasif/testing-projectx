import streamlit as st
from Components.gdrive_database.gdrive_conn import googleConnect
from Components.gdrive_database.googledrive_ID import SCOPE_ID, SERVICE_ACC_ID, PARENT_FOLDER

st.set_page_config(page_title='QA ProjectX', layout='wide')

# Configuration
SERVICE_ACCOUNT_FILE = SERVICE_ACC_ID
SCOPES = SCOPE_ID
PARENT_FOLDER_ID = PARENT_FOLDER

# Instantiate the googleConnect class
driveAPI = googleConnect(SERVICE_ACCOUNT_FILE, SCOPES, PARENT_FOLDER_ID)

# Get a list of files
listFiles = driveAPI.get_list_files()

fileName = [name for name, id, time in listFiles]
st_selectFile = st.selectbox('Select a file', fileName)

if st_selectFile:
    selectedFile = [(fileID, modifiedTime) for name, fileID, modifiedTime in listFiles if name == st_selectFile][0] # Storing only id and modified time (name is neglected)
    selectedFile_ID = selectedFile[0]
    lastUpdated_time = selectedFile[1]
    fileData = driveAPI.read_file_from_drive(selectedFile_ID)

