import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

@st.cache_resource
def authenticate(service_account_file, scopes):
    '''
    Authenticate the account for Google Drive access.
    '''
    return service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )

@st.cache_resource
def get_drive_service(_creds):
    '''
    Initialize the Google Drive API service using provided credentials.
    '''
    return build('drive', 'v3', credentials=_creds)


@st.cache_data
def get_list_files(_service, parent_folder_id):
    '''
    Retrieve a list of files from Google Drive, including names, file IDs, and last modified timestamps.
    '''
    results = _service.files().list(
        q=f"'{parent_folder_id}' in parents",
        spaces='drive',
        fields='nextPageToken, files(id, name, modifiedTime)'
    ).execute()

    items = results.get('files', [])
    return [
        (item['name'], item['id'], item['modifiedTime']) for item in items
    ] if items else []


class googleConnect:
    def __init__(self, service_account_file, scopes, parent_folder_id):
        self.service_account_file = service_account_file
        self.scopes = scopes
        self.parent_folder_id = parent_folder_id
        self.creds = authenticate(service_account_file, scopes)
        self.service = get_drive_service(self.creds)

    def get_list_files(self):
        '''
        Wrapper for get_list_files function.
        '''
        return get_list_files(self.service, self.parent_folder_id)

    def read_file_from_drive(self, file_id):
        '''
        Read an Excel file from Google Drive.
        '''
        request = self.service.files().get_media(fileId=file_id)
        file_data = BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        file_data.seek(0)
        return file_data
