## 구글 스프레드시트 연동과 관련한 내용은 여기서 중앙관리 

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# Scope for Google Sheets API
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def connect_to_sheet():
    """
    Connects to Google Sheets using Streamlit secrets.
    """
    try:
        # Expecting secrets to be set in .streamlit/secrets.toml
        # [gcp_service_account]
        # type = "service_account"
        # ...
        
        # If running locally without secrets, you might rely on a local file or environment var.
        # This implementation assumes st.secrets is populated.
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        elif os.path.exists('credentials.json'):
             # Fallback for local testing if credentials.json exists
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
        else:
            st.error("❌ Credentials not found! Please set up `.streamlit/secrets.toml` or place `credentials.json` in the root directory.")
            return None
            
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def load_data(sheet_url_or_id: str, worksheet_name: str = 0) -> pd.DataFrame:
    """
    Loads data from a specific worksheet.
    worksheet_name can be an index (int) or name (str).
    """
    client = connect_to_sheet()
    if not client:
        return pd.DataFrame() # Return empty on failure
        
    try:
        sheet = client.open_by_key(sheet_url_or_id) if len(sheet_url_or_id) > 20 else client.open(sheet_url_or_id)
        
        if isinstance(worksheet_name, int):
            ws = sheet.get_worksheet(worksheet_name)
        else:
            try:
                # Try opening by name first
                ws = sheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                # If failed, check if it's a GID (numeric string or int)
                try:
                    target_gid = int(worksheet_name)
                    # Iterate to find matching GID
                    ws = next((w for w in sheet.worksheets() if w.id == target_gid), None)
                    if ws is None:
                        raise gspread.WorksheetNotFound(f"GID {target_gid} not found")
                except ValueError:
                     raise gspread.WorksheetNotFound(f"Worksheet '{worksheet_name}' not found")
            
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

def save_snapshot(sheet_url_or_id: str, df: pd.DataFrame, master_worksheet_name: str = "Sheet1"):
    """
    Saves the dataframe to the master sheet and creates a snapshot sheet.
    """
    client = connect_to_sheet()
    if not client:
        return False

    try:
        sheet = client.open_by_key(sheet_url_or_id) if len(sheet_url_or_id) > 20 else client.open(sheet_url_or_id)
        
        # 1. Update Master Sheet
        try:
            ws_master = sheet.worksheet(master_worksheet_name)
        except:
            ws_master = sheet.get_worksheet(0) # Helper fallback
            
        # Clear and update is simple but risky for formulas. 
        # Requirement says: "sujung contents". Assuming we push the full DF.
        ws_master.clear()
        ws_master.update([df.columns.values.tolist()] + df.values.tolist())
        
        # 2. Create Snapshot
        snapshot_name = datetime.now().strftime("%Y-%m-%d_%H%M")
        try:
             ws_snapshot = sheet.add_worksheet(title=snapshot_name, rows=len(df)+100, cols=len(df.columns)+5)
             ws_snapshot.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.warning(f"Snapshot creation failed (might already exist): {e}")

        return True
        
    except Exception as e:
        st.error(f"Failed to save data: {e}")
        return False
