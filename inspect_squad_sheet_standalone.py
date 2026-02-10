
import toml
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import sys

def inspect():
    try:
        print("Starting standalone inspection...")
        secrets_path = '.streamlit/secrets.toml'
        if not os.path.exists(secrets_path):
            print(f"Secrets file not found at {secrets_path}")
            return

        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
            
        if "gcp_service_account" not in secrets:
            print("gcp_service_account not found in secrets.")
            return

        creds_dict = secrets["gcp_service_account"]
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        print("Connected to Google Sheets.")
        
        sheet_id = '1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts'
        gid = '2103927428'
        
        sheet = client.open_by_key(sheet_id)
        print(f"Opened sheet: {sheet.title}")
        
        target_gid = int(gid)
        ws = next((w for w in sheet.worksheets() if w.id == target_gid), None)
        
        if not ws:
            print(f"Worksheet with GID {gid} not found.")
            return
            
        print(f"Found worksheet: {ws.title}")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        print("Columns found:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
        
        with open("inspection_result_standalone.txt", "w", encoding="utf-8") as f:
            f.write(f"Columns: {df.columns.tolist()}\n")
            f.write(f"Head:\n{df.head().to_string()}\n")
            
    except Exception as e:
        print(f"Error: {e}")
        with open("inspection_result_standalone.txt", "w", encoding="utf-8") as f:
             f.write(f"Error: {e}")

if __name__ == "__main__":
    inspect()
