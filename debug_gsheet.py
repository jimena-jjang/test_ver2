import streamlit as st
import pandas as pd
from gsheet_handler import load_data, connect_to_sheet
import os

def debug_sheet():
    print("1. Checking Credentials...")
    client = connect_to_sheet()
    if client:
        print("✅ Credentials found and client authorized.")
    else:
        print("❌ Failed to connect. Check secrets or credentials.json.")
        return

    sheet_id = "1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts"
    gid = "311390646"

    print(f"\n2. Loading Data from ID: {sheet_id}, GID: {gid}...")
    try:
        df = load_data(sheet_id, gid)
        if df.empty:
            print("❌ Data loaded but DataFrame is empty.")
        else:
            print("✅ Data loaded successfully!")
            print(f"Shape: {df.shape}")
            print("Columns:", df.columns.tolist())
            print("First 3 rows:")
            print(df.head(3))
            
            print("\n3. Testing Process Resource Dataframe...")
            from utils import process_resource_dataframe
            processed = process_resource_dataframe(df)
            if processed is not None:
                print("✅ Processing successful!")
                print(processed.head(3))
            else:
                print("❌ Processing failed (returned None). Check column names.")

    except Exception as e:
        print(f"❌ Exception during load: {e}")

if __name__ == "__main__":
    debug_sheet()
