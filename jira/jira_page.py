
import pandas as pd
import numpy as np
import streamlit as st
from jira.jira_secrets import JIRA_EMAIL_SECRET, JIRA_TOKEN_SECRET, JIRA_URL_SECRET

# # testing display table
# from st_aggrid import AgGrid, GridOptionsBuilder

# testing JIRA

def display_jira_page():

    # st.subheader("Example use of JIRA API")

    
    # st.title('------------------------------------------------')
    
    # import requests
    # from requests.auth import HTTPBasicAuth

    # # JIRA credentials
    # JIRA_EMAIL = JIRA_EMAIL_SECRET
    # JIRA_TOKEN = JIRA_TOKEN_SECRET
    # JIRA_URL = JIRA_URL_SECRET  # Change this to match your JIRA base URL

    # # Define JQL query (example: issues in project RS1 created in November 2024)
    # jql_query = 'project = "RS1" AND created >= "2024-11-05" AND created <= "2024-11-11" ORDER BY created DESC'

    # # Make the request
    # def get_jira_issues():
    #     headers = {
    #         "Accept": "application/json"
    #     }
    #     params = {
    #         "jql": jql_query
    #     }
    #     response = requests.get(JIRA_URL, headers=headers, params=params, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN))
    #     return response.json() if response.status_code == 200 else None

    # # Streamlit display
    # st.title("JIRA Issues Viewer")
    # issues = get_jira_issues()

    # if issues:
    #     for issue in issues['issues']:
    #         st.write(f"Issue Key: {issue['key']}")
    #         st.write(f"Summary: {issue['fields']['summary']}")
    #         st.write(f"Created: {issue['fields']['created']}")
    #         st.write("---")
    # else:
    #     st.error("Failed to retrieve issues from JIRA.")



    if __name__ == "__main__":
        display_jira_page()



