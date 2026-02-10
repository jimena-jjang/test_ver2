
import streamlit as st
import pandas as pd
from gsheet_handler import connect_to_sheet
import sys
import os

try:
    print("Starting inspection...")
    sheet_id = '1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts'
    gid = '2103927428'
    
    # gsheet_handler.connect_to_sheet uses st.secrets
    client = connect_to_sheet()
    
    if client:
        sheet = client.open_by_key(sheet_id)
        target_gid = int(gid)
        ws = next((w for w in sheet.worksheets() if w.id == target_gid), None)
        
        if ws:
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            with open("inspection_result.txt", "w", encoding="utf-8") as f:
                f.write(f"Columns: {df.columns.tolist()}\n")
                f.write(f"Head:\n{df.head().to_string()}\n")
                print("Inspection successful. Result written to inspection_result.txt")
        else:
            with open("inspection_result.txt", "w", encoding="utf-8") as f:
                f.write(f"Worksheet output not found for GID: {gid}")
            print("Worksheet not found.")
    else:
        with open("inspection_result.txt", "w", encoding="utf-8") as f:
            f.write("Failed to connect via connect_to_sheet.")
        print("Failed to connect.")

except Exception as e:
    with open("inspection_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
    print(f"Error: {e}")

# Stop the script logic
os._exit(0)
