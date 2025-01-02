import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from googledrive_ID import SCOPE_ID, SERVICE_ACC_ID, PARENT_FOLDER

from googleapiclient.discovery import build
from google.oauth2 import service_account
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload

import plotly.graph_objects as go
import plotly.express as px

from matplotlib.colors import to_rgba

from datetime import datetime
import pytz

import textwrap

SCOPES = SCOPE_ID
SERVICE_ACCOUNT_FILE = SERVICE_ACC_ID
PARENT_FOLDER_ID = PARENT_FOLDER

@st.cache_data
def authenticate():
    '''
    Autentikasi akun untuk akses ke gdrive
    '''
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

@st.cache_data
def get_list_files():
    '''
    Get list of files dari gdrive, termasuk nama, id filenya, sama terakhir kali di-modify
    '''
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    results = service.files().list(
        q=f"'{PARENT_FOLDER_ID}' in parents",
        spaces='drive',
        fields='nextPageToken, files(id, name, modifiedTime)'
    ).execute()
    
    items = results.get('files', [])
    
    list_file = []
    if items:
        list_file = [(item['name'], item['id'], item['modifiedTime']) for item in items]
    return list_file

@st.cache_data
def read_file_from_drive(file_id):
    '''
    Read Excel file from Google Drive
    '''
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    # Stream the file content
    request = service.files().get_media(fileId=file_id)
    file_data = BytesIO()
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    file_data.seek(0)
    return file_data  # Return the raw file data


@st.cache_data
def processing_excel(file_data, sheet_name):
    '''
    Process Excel file to clean and prepare the data
    '''
    
    excel_ptr = pd.read_excel(file_data, sheet_name, header=None)
    temp_df = excel_ptr.ffill()
    
    listof_ver = temp_df[temp_df[1].str.contains('PTR Ver', na=False)][1].unique().tolist()
    
    # Get the rows which will become header
    value_to_skip = 'Features'
    max_rows_to_scan = 10

    header_index = excel_ptr.head(max_rows_to_scan).apply(lambda row: row.astype(str).str.contains(value_to_skip).any(), axis=1).idxmax()

    if pd.isna(header_index):  # If 'Features' wasn't found in the scanned rows
        print("Header 'Features' not found in the first", max_rows_to_scan, "rows.")
    else:
        new_header = excel_ptr.iloc[header_index].values
        excel_ptr = excel_ptr.iloc[header_index+1:].copy()
        excel_ptr.columns = new_header
        
    excel_ptr = excel_ptr.iloc[:, 1:]
    excel_ptr.reset_index(drop=True, inplace=True)
    
    # Convert column OS Version types
    if 'OS Version' not in excel_ptr.columns:
        st.stop()
    else:
        excel_ptr['OS Version'] = excel_ptr['OS Version'].astype(str)
    
    # drop column Number
    excel_ptr.drop(columns='No', inplace=True, errors='ignore')
    
    #Rename the column
    excel_ptr.rename(columns={
        'Sub Fitur': 'Sub-features',
        'Rekening Sumber\n[Jika ada]': 'Rekening Sumber',
        'Data yang Digunakan\n[Jika ada]': 'Data yang digunakan',
        'FT\n[Jika Ada]': 'FT',
        'Tanggal Eksekusi\n[harus diisi]': 'Tanggal Eksekusi',
        'Tanggal Passed\n[harus diisi]': 'Tanggal Passed'
    }, inplace=True)
    
    # Because of merged and centered, need to use ffill to duplicate values before current rows
    excel_ptr[['Features', 'Sub-features', 'Expected Condition']] = excel_ptr[['Features', 'Sub-features', 'Expected Condition']].apply(lambda x: x.ffill())
    
    return excel_ptr, listof_ver

@st.cache_data
def progress_status(df, version):
    df_android = df[df['OS'] == 'Android'].copy()
    df_ios = df[df['OS'] == 'iOS'].copy()

    android_result = df_android['Status ' + version].value_counts(normalize=True) * 100
    ios_result = df_ios['Status ' + version].value_counts(normalize=True) * 100
    
    df_plot = pd.concat([android_result.rename("Android"), ios_result.rename('iOS')], axis=1).reset_index()
    df_plot.rename(columns={'Status '+version : 'Status'}, inplace=True)
    
    df_plot = df_plot.melt(id_vars='Status', var_name='Platform', value_name='Percentage')
    df_plot['Percentage'] = df_plot['Percentage'].apply(lambda row: round(row, 2))

    return df_plot

def progress_plot(df_plot):
    progress_bar = px.bar(
        df_plot,
        x="Status",
        y="Percentage",
        color="Platform",
        barmode="group",
        text="Percentage",
        color_discrete_map={"Android": "#71BC68", "iOS": "rgba(70, 130, 180, 0.8)"}  # Custom colors
    )

    # Customize the traces for better readability
    progress_bar.update_traces(
        texttemplate='%{text:.2f}%',
        textposition='outside',
        marker=dict(cornerradius='30%' ,line=dict(width=1.5, color="black"))  # Add a border to bars
    )

    # Update layout for a cleaner and professional look
    progress_bar.update_layout(
        xaxis=dict(
            title="<b style='color: #ffbd44;'>Status</b>",
            tickfont=dict(size=12, family="Arial, sans-serif"),
        ),
        yaxis=dict(
            title="<b style='color: #ffbd44;'>Percentage (%)</b>",
            tickfont=dict(size=12, family="Arial, sans-serif"),
        ),
        legend=dict(
            title="<b> </b>",
            font=dict(size=12, family="Arial, sans-serif"),
            bgcolor="#1E1E1E",  # Light gray background for legend
            borderwidth=0,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font_size=16
        ),
        margin=dict(l=50, r=50, t=30, b=0),  # Adjust margins for spacing
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot background
        paper_bgcolor="#1E1E1E",  # Light gray background
        font_size=16,
        width=1000,
        height=500
    )
    
    return progress_bar


def wrap_text(text, width=20):
    return '\n'.join(textwrap.wrap(text, width))

def display_tester_page():
    with st.expander(label='Filter'):
        with st.container():
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                list_files = get_list_files()
                if not list_files:
                    st.warning('Sorry! No files found in specified folder')
                else:
                    file_name = [name for name, _, _ in list_files]
                    selected_file = st.selectbox('Select a file', file_name)
                    
                if selected_file:
                    selected_file_data = [(file_id, modified_time) for name, file_id, modified_time in list_files if name == selected_file][0]
                    selected_file_id = selected_file_data[0]
                    last_updated_time = selected_file_data[1]
                    
                    utc_time = datetime.strptime(last_updated_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                    jakarta_tz = pytz.timezone('Asia/Jakarta')
                    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(jakarta_tz)
                    formatted_time = local_time.strftime("%d %b %Y, %H:%M %p")
                    
                    # Get the raw file data
                    file_data = read_file_from_drive(selected_file_id)
                    
                    # Load the Excel file to access sheets
                    excel_ptr = pd.ExcelFile(file_data)
                    sheet_names = excel_ptr.sheet_names

                if st.button('Refresh', type='secondary'):
                    st.cache_data.clear()
            
            with col2:
                try:
                    if 'excel_ptr' in locals() and 'sheet_names' in locals():  # Check if these are defined
                        select_sheet = st.selectbox('Select a sheet', sheet_names)
                            
                        if select_sheet:
                            excel_ptr, ptr_versions = processing_excel(file_data, sheet_name=select_sheet)
                            ptr_versions = [str(i).replace('\n', ' ') for i in ptr_versions]
                except:
                    st.error('The selected sheet does not have standard format')
                    st.stop()
            
            with col3:
                try:
                    # Select PTR version
                    select_ptr_version = st.selectbox('Select a PTR version', ptr_versions)
                    
                    if select_ptr_version:
                        # Attempt to perform the operation that caused the error
                        column_name = "Status " + select_ptr_version
                        excel_ptr[column_name] = excel_ptr[column_name].replace(np.nan, 'N/A')
                except:
                    st.stop()


    # SANKEY DIAGRAM
    # Create nodes and flows
    try:
        nodes = list(set(
            excel_ptr['Features'].tolist() +
            excel_ptr['Sub-features'].tolist() +
            excel_ptr['OS'].tolist() +
            excel_ptr['OS Version'].tolist() +
            excel_ptr['Tipe Device HP'].tolist() +
            excel_ptr["Status "+ select_ptr_version].tolist()
        ))

        def wrap_long_name(name, width=50):
            return '<br>'.join(textwrap.wrap(str(name), width))

        # Create short labels for Sankey plot without modifying the original df
        node_indices = {
            node: (str(node)[:30] + "...") if isinstance(node, str) and len(str(node)) > 30 else str(node)
            for node in nodes
        }

        # Create a list of shortened node labels for the Sankey plot
        short_nodes = [node_indices[node] for node in nodes]
        long_nodes = [wrap_long_name(node) for node in nodes]

        # Create flows (source → target)
        sources = []
        targets = []
        values = []

        # Generate sources and targets for the Sankey diagram
        for _, row in excel_ptr.iterrows():
            feature = row["Features"]
            sub_feature = row["Sub-features"]
            status = row["Status "+ select_ptr_version]
            os_type = row["OS"]

            # Feature -> Status -> OS if Status is "Passed"
            if status == "Passed":
                sources.append(nodes.index(feature))  # Feature -> Status
                targets.append(nodes.index(status))
                values.append(1)
                
                # sources.append(nodes.index(sub_feature))  # Sub-feature -> Status
                # targets.append(nodes.index(status))
                # values.append(1)

                sources.append(nodes.index(status))  # Status -> OS
                targets.append(nodes.index(os_type))
                values.append(1)

            # Feature -> Sub-feature -> Status -> OS if Status is "Failed"
            elif status == "Failed" or status == "N/A" or status == "In Progress" or status == "Not Started":
                sources.append(nodes.index(feature))  # Feature -> Sub-feature
                targets.append(nodes.index(sub_feature))
                values.append(1)

                sources.append(nodes.index(sub_feature))  # Sub-feature -> Status
                targets.append(nodes.index(status))
                values.append(1)

                sources.append(nodes.index(status))  # Status -> OS
                targets.append(nodes.index(os_type))
                values.append(1)
                
            # Calculate incoming and outgoing flows
            incoming_flows = {node: 0 for node in nodes}
            outgoing_flows = {node: 0 for node in nodes}

            for source, target in zip(sources, targets):
                outgoing_flows[nodes[source]] += 1  # Increase the outgoing flow count for the source node
                incoming_flows[nodes[target]] += 1  # Increase the incoming flow count for the target node

            # Prepare customdata with both incoming and outgoing flows
            customdata = [
                f"{long_name} <br>Incoming: {incoming_flows[node]} <br>Outgoing: {outgoing_flows[node]}"
                for node, long_name in zip(nodes, long_nodes)
            ]
                
            # Assign a default value of 1 for each connection
            values = [1] * len(sources)

            # Use a qualitative color scale for high contrast (e.g., Plotly's 'Dark24')
            color_palette = px.colors.qualitative.Light24 # Replace with another palette if needed
            num_colors = len(color_palette)

            opacity = 1  # Example opacity value (0.0 - 1.0)
            node_colors = {}
            for i, feature in enumerate(excel_ptr["Features"].unique()):
                hex_color = color_palette[i % num_colors]  # Get the hex color
                rgba_color = to_rgba(hex_color, alpha=opacity)  # Convert to RGBA
                node_colors[feature] = f"rgba({int(rgba_color[0]*255)}, {int(rgba_color[1]*255)}, {int(rgba_color[2]*255)}, {rgba_color[3]})"

            # Propagate feature colors to sub-features
            for feature in excel_ptr["Features"].unique():
                feature_color = node_colors[feature]
                for sub_feature in excel_ptr[excel_ptr["Features"] == feature]["Sub-features"].unique():
                    node_colors[sub_feature] = "rgba(200, 200, 200, 0.8)"

            # Overwrite colors for 'Passed' and 'Failed'
            node_colors["Passed"] = "rgba(144, 238, 144, 0.8)"  # Soft green
            node_colors["Failed"] = "rgba(205, 92, 92, 0.8)"    # Soft red brick

            node_colors["Android"] = "#71BC68"  # Green turquoise
            node_colors["iOS"] = "rgba(70, 130, 180, 0.8)"      # Steel blue

            # Set default color for unassigned nodes
            default_color = "rgba(200, 200, 200, 0.8)"
            node_color_list = [node_colors.get(node, default_color) for node in nodes]

            # Assign link colors based on source node color with transparency
            link_colors = []
            for source, target in zip(sources, targets):
                source_color = node_colors.get(nodes[source], "rgba(192, 192, 192, 0.3)")  # Default gray if missing
                rgba_values = source_color.strip("rgba()").split(",")
                if len(rgba_values) == 4:
                    r, g, b, _ = map(float, rgba_values[:4])
                    link_colors.append(f"rgba({int(r)}, {int(g)}, {int(b)}, 0.3)")  # Reduce opacity for the links
                else:
                    link_colors.append("rgba(192, 192, 192, 0.3)")  # Default gray


        # Plot Sankey Diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=short_nodes,  # Use short labels here
                color=node_color_list,  # Optionally set a default color
                customdata=customdata,
                hovertemplate="%{customdata}<extra></extra>"
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors
            )
        )])

        # Update layout and show
        fig.update_layout(
            font_size=12,
            # width=500,  # Increase width for a wider graph
            height=700,   # Increase height for a taller graph
            font=dict(size=14, color='white'),
            plot_bgcolor='#1E1E1E',
            paper_bgcolor='#1E1E1E',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
    except:
        st.error("Sorry, your selected file does not have a correct standard format.")
        st.stop()


    #showing table
    
    status_cell_style_js = JsCode('''
    function(params) {
        if (params.value === 'Failed') {
            return {
                'color': 'white',
                'backgroundColor': 'red',
                'fontWeight': 'bold',
            };
        } else if (params.value === 'Passed') {
            return {
                'color': 'white',
                'backgroundColor': 'green',
                'fontWeight': 'bold',
            };
        } else if (params.value === 'In Progress') {
            return {
                'color': 'white',
                'backgroundColor': 'blue',
                'fontWeight': 'bold',
            };
        } else if (params.value === 'N/A') {
            return {
                'color': 'black',
                'backgroundColor': 'yellow',
                'fontWeight': 'bold',
            };
        }
        return null;  // Default styling
    }
''')

    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(excel_ptr)
    gb.configure_default_column(resizable=True, filterable=True, sortable=True, editable=True)
    
    # styling for parent columns
    gb.configure_column("Features", rowGroup=True, hide=True)
    gb.configure_column("Sub-features", rowGroup=True, hide=True)
    gb.configure_column("Expected Condition", rowGroup=True, hide=True)
    
    # styling for status column
    gb.configure_column("Status " + select_ptr_version, cellStyle=status_cell_style_js)
    
    # panigantion, selection box, and autosize
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_grid_options(
        groupDefaultExpanded=-1,
        suppressColumnVirtualisation=True,
        groupDisplayType="groupRows"
    )
    
    
    tab1, tab2 = st.tabs(['Dashboard', 'Data Sheet'])
    
    with tab1:
        
        
        st.markdown(' ')
        
        st.markdown(f"""
                    <div style='margin-bottom: 10px; font-size: 25px;'>
                        <b style="color: #ffbd44;">{select_sheet}</b>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Display time modified fot selected file data
        st.markdown(f"""
                    <div style='margin-bottom: -10px;'>
                        <b style="color: #ffbd44;">Version:</b> {select_ptr_version}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown(f"**:orange[Last updated time:]** {formatted_time}")
        
        st.markdown(':gray[A side project fully coded by [Nahari Rasif](%s)]' % 'https://www.linkedin.com/in/naharirasif/')

        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        
        col1, col2, col3, col4, col5, col6= st.columns(6)
        
        col1.metric(label="Execution Rate", value="87%", border=True)
        col2.metric(label="Passed", value="53%", border=True)
        col3.metric(label="Failed", value="4%", border=True)
        col4.metric(label="In Progress", value="11%", border=True)
        col5.metric(label="Not Started", value="12%", border=True)
        col6.metric(label="N/A", value="7%", border=True)
        
        with st.container():
            col1, col2 = st.columns([1,1])
            with col1:
                st.markdown(' ')
                st.markdown(f"""
                            <div style='margin-bottom: -20px; font-size: 20px; text-align: center;'>
                                <b style="color: #ffbd44;">Cumulative Progress</b>
                            </div>
                            """, unsafe_allow_html=True)
                
                df_plot = progress_status(df=excel_ptr, version=select_ptr_version)
                progress_bar = progress_plot(df_plot=df_plot)
                
                st.plotly_chart(progress_bar, use_container_width=True)
                
            with col2:
                st.markdown(' ')
                years = ['2016', '2017', '2018']

                vert_graph = go.Figure()
                vert_graph.add_trace(go.Bar(x=years, y=[500, 600, 700],
                                            base=[-500, -600, -700],
                                            marker_color='crimson',
                                            name='expenses',
                                            orientation='h'))  # Horizontal orientation
                vert_graph.add_trace(go.Bar(x=years, y=[300, 400, 700],
                                            base=0,
                                            marker_color='lightslategrey',
                                            name='revenue',
                                            orientation='h'))  # Horizontal orientation

                # Set title and legend to center
                vert_graph.update_layout(
                    title={
                        'text': "<b>Financial Overview</b>",  # Example title
                        'y': 0.9,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        font_size=16
                    )
                )

                st.plotly_chart(vert_graph, use_container_width=True)
                                

    with tab2:
        AgGrid(
            excel_ptr, 
            gridOptions=gb.build(), 
            height=900, 
            theme="alpine",
            allow_unsafe_jscode=True,
            # enable_enterprise_modules = True,
            # fit_columns_on_grid_load = True
        )

if __name__ == "__main__":
    display_tester_page()
