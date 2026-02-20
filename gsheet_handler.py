## 구글 스프레드시트 연동과 관련한 내용은 여기서 중앙관리 

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import unicodedata

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
            st.error("❌ Google Sheets Connection Error: `gcp_service_account` not found in `secrets.toml` and `credentials.json` missing.")
            # For debugging, list available keys (safe subset)
            st.error(f"Available secrets keys: {list(st.secrets.keys())}")
            return None
            
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def _get_worksheet(sheet, worksheet_name):
    """
    Helper to find a worksheet by name, index, or GID.
    """
    try:
        # First, check if it matches a GID exactly (as string or int)
        target_gid_str = str(worksheet_name)
        for w in sheet.worksheets():
            if str(w.id) == target_gid_str:
                return w
                
        # If not a GID, try treating it as an index if it's an int
        if isinstance(worksheet_name, int):
            try:
                return sheet.get_worksheet(worksheet_name)
            except Exception:
                pass
        
        # Finally, try finding by name
        try:
            return sheet.worksheet(str(worksheet_name))
        except gspread.WorksheetNotFound:
            pass
            
        st.error(f"❌ Worksheet '{worksheet_name}' not found.")
        return None
        
    except Exception as e:
        st.error(f"❌ Error finding worksheet: {e}")
        return None

@st.cache_data(ttl=600)
def load_data(sheet_url_or_id: str, worksheet_name: str = 0) -> pd.DataFrame:
    """
    Loads data from a specific worksheet.
    worksheet_name can be an index (int) or name (str).
    """
    # st.toast("Connecting to Google Sheets...") # Removed to avoid CacheReplayClosureError
    print(f"DEBUG: load_data called for {sheet_url_or_id} / {worksheet_name}")
    client = connect_to_sheet()
    if not client:
        return pd.DataFrame() # Return empty on failure
        
    try:
        # Try opening sheet
        try:
             sheet = client.open_by_key(sheet_url_or_id) if len(sheet_url_or_id) > 20 else client.open(sheet_url_or_id)
        except gspread.SpreadsheetNotFound:
             st.error(f"❌ Spreadsheet not found. Check ID: {sheet_url_or_id}")
             # print(f"Spreadsheet not found: {sheet_url_or_id}")
             return pd.DataFrame()
        except Exception as e:
             st.error(f"❌ Error opening spreadsheet: {e}")
             # print(f"Error opening spreadsheet: {e}")
             return pd.DataFrame()
        
             st.error(f"❌ Error opening spreadsheet: {e}")
             # print(f"Error opening spreadsheet: {e}")
             return pd.DataFrame()
        
        # Try finding worksheet
        ws = _get_worksheet(sheet, worksheet_name)
        
        if ws:     
            # st.toast("Fetching data...")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            if df.empty:
                 st.warning("⚠️ Worksheet is empty.")
                 # print("Worksheet is empty.")
            return df
        else:
             return pd.DataFrame()

    except Exception as e:
        st.error(f"Failed to load data (Unexpected): {e}")
        # print(f"Failed to load data (Unexpected): {e}")
        return pd.DataFrame()

def save_snapshot(sheet_url_or_id: str, df: pd.DataFrame, master_worksheet_name: str = "Sheet1"):
    """
    Saves the dataframe to the master sheet and creates a snapshot sheet.
    """
    client = connect_to_sheet()
    if not client:
        return False

    try:
        # Pre-connection check for sheet availability (though open happens later usually)
        # Moved open logic here to fail fast if connection bad, 
        # but the main safety is about data preparation.
        
        sheet = client.open_by_key(sheet_url_or_id) if len(sheet_url_or_id) > 20 else client.open(sheet_url_or_id)
        
        # ---------------------------------------------------------------------
        # SAFE SERIALIZATION LOGIC (CRITICAL FIX)
        # ---------------------------------------------------------------------
        # Create a copy to avoid modifying the displayed DF safely
        df_to_save = df.copy()
        print(f"DEBUG: Saving data to {master_worksheet_name}. Shape: {df_to_save.shape}")
        
        # [Fix] Convert Categorical types to Object to prevent "Cannot setitem with new category" error
        # This allows inserting empty strings or new values that aren't in the original categories.
        for col in df_to_save.columns:
            if isinstance(df_to_save[col].dtype, pd.CategoricalDtype):
                df_to_save[col] = df_to_save[col].astype(object)

        # Helper to convert dates safely
        def serialize_date(val):
            if pd.isna(val) or val == "" or str(val).lower() == 'nat':
                return ""
            try:
                if isinstance(val, (pd.Timestamp, datetime)):
                    return val.strftime("%Y-%m-%d")
                return str(val)[:10] # Fallback
            except:
                return ""

        # Ensure all date columns are converted to strings properly
        date_cols = ['Start', 'End']
        for col in date_cols:
            if col in df_to_save.columns:
                 df_to_save[col] = df_to_save[col].apply(serialize_date)
                 
        # Fill strictly NaNs (for non-date columns) with empty string for JSON safety
        df_to_save = df_to_save.fillna("")
        
        # Prepare the data payload FIRST (Validation Step)
        # This converts DataFrame to the List[List] format gspread expects.
        # If this fails (e.g. still some non-serializable object), exception raises HERE.
        data_to_upload = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
        
        # ---------------------------------------------------------------------
        # DATA UPDATE (SAFE COMMIT)
        # ---------------------------------------------------------------------
        # Only reached if data preparation succeeded.
        
        # 1. Update Master Sheet
        # 1. Update Master Sheet
        ws_master = _get_worksheet(sheet, master_worksheet_name)
        
        if not ws_master:
            ws_master = sheet.get_worksheet(0) # Helper fallback
            st.warning(f"Could not find worksheet '{master_worksheet_name}'. Saving to first worksheet '{ws_master.title}' instead.")
            
        # NOW it is safe to clear
        ws_master.clear()
        ws_master.update(data_to_upload)
        
        # 2. Create Snapshot - DISABLED per user request
        # snapshot_name = datetime.now().strftime("%Y-%m-%d_%H%M")
        # try:
        #      ws_snapshot = sheet.add_worksheet(title=snapshot_name, rows=len(df)+100, cols=len(df.columns)+5)
        #      ws_snapshot.update(data_to_upload)
        # except Exception as e:
        #     # Snapshot failure is non-critical, just warn
        #     st.warning(f"Snapshot creation failed (might already exist): {e}")


    
        # Clear cache to ensure next load gets fresh data
        st.cache_data.clear()
        print("DEBUG: Cache cleared after save.")
        return True

    except Exception as e:
        st.error(f"Failed to save data: {e}")
        return False

@st.cache_data(ttl=600)
def load_squad_order_from_sheet(sheet_id: str, worksheet_gid: str):
    """
    Loads squad order from a specific Google Sheet GID.
    Expected columns: 'squad', 'order' (case-insensitive).
    Returns a list of squad names sorted by order.
    """
    try:
        # st.write(f"DEBUG: load_squad_order_from_sheet called for {sheet_id}, GID {worksheet_gid}")
        
        client = connect_to_sheet()
        if not client:
            st.error("DEBUG: Failed to connect to sheet.")
            return []
            
        sheet = client.open_by_key(sheet_id)
        
        # Helper to find by GID with robust string comparison
        ws = None
        target_gid_str = str(worksheet_gid)
        
        try: 
            all_ws = sheet.worksheets()
            for w in all_ws:
                if str(w.id) == target_gid_str:
                    ws = w
                    break
                    
            if not ws:
                st.warning(f"DEBUG: Worksheet GID {worksheet_gid} not found. Available GIDs: {[w.id for w in all_ws]}")
                return []
                
        except Exception as e:
             st.error(f"DEBUG: Error iterating worksheets: {e}")
             return []
        
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            st.warning("DEBUG: Worksheet is empty.")
            return []
            
        # Normalize columns
        df.columns = df.columns.astype(str).str.strip().str.lower()
        
        # Identify relevant columns
        squad_col = next((c for c in df.columns if 'squad' in c or '스쿼드' in c), None)
        order_col = next((c for c in df.columns if 'order' in c or '순서' in c or '정렬' in c), None)
        
        if not squad_col:
            st.error(f"DEBUG: Squad column not found. Columns: {df.columns.tolist()}")
            return []
            
        # If order column exists, sort by it. Otherwise, assume file order.
        if order_col:
            df[order_col] = pd.to_numeric(df[order_col], errors='coerce').fillna(9999)
            df = df.sort_values(by=order_col)
        
        # Extract unique squads
        squad_list = df[squad_col].dropna().astype(str).str.strip().unique().tolist()
        
        # Normalize NFC
        squad_list = [unicodedata.normalize('NFC', s) for s in squad_list]
        
        # st.success(f"DEBUG: Loaded {len(squad_list)} squads.")
        return squad_list
        
    except Exception as e:
        st.error(f"DEBUG: Fatal error loading squad order: {e}")
        return []
