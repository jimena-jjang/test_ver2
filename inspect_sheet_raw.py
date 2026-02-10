
import streamlit as st
import pandas as pd
import gsheet_handler
import gspread

st.set_page_config(layout="wide")
st.title("🕵️ Raw Sheet Inspector")

SHEET_ID = '1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts'
TARGET_GID = '2103927428'

st.write(f"**Target Sheet ID:** `{SHEET_ID}`")
st.write(f"**Target GID:** `{TARGET_GID}`")

try:
    client = gsheet_handler.connect_to_sheet()
    if not client:
        st.error("❌ Failed to connect to Google Sheets (Client is None). check .streamlit/secrets.toml")
        st.stop()
    
    st.success("✅ Connected to Google Sheets API")
    
    try:
        sheet = client.open_by_key(SHEET_ID)
        st.success(f"✅ Opened Spreadsheet: **{sheet.title}**")
        
        # List all worksheets
        st.subheader("Available Worksheets")
        worksheets = sheet.worksheets()
        
        ws_data = []
        target_ws = None
        
        for ws in worksheets:
            is_target = str(ws.id) == str(TARGET_GID)
            ws_data.append({
                "Title": ws.title,
                "ID (GID)": str(ws.id),
                "Is Target?": "✅ YES" if is_target else ""
            })
            if is_target:
                target_ws = ws
                
        st.table(ws_data)
        
        if target_ws:
            st.subheader(f"📄 Inspecting Target Worksheet: `{target_ws.title}`")
            
            # Fetch all records
            data = target_ws.get_all_records()
            df = pd.DataFrame(data)
            
            st.write(f"**Shape:** {df.shape}")
            
            if df.empty:
                st.warning("⚠️ The worksheet is empty!")
            else:
                st.write("**Raw Columns found:**", df.columns.tolist())
                
                # Check for desired columns
                st.write("**Data Preview:**")
                st.dataframe(df.head(20))
                
                # Column check logic similar to gsheet_handler
                df.columns = df.columns.astype(str).str.strip().str.lower()
                squad_col = next((c for c in df.columns if 'squad' in c or '스쿼드' in c), None)
                order_col = next((c for c in df.columns if 'order' in c or '순서' in c or '정렬' in c), None)
                
                st.write("---")
                st.write("### Logic Check:")
                if squad_col:
                    st.success(f"✅ Found Squad Column: `{squad_col}`")
                else:
                    st.error("❌ Squad Column NOT FOUND (looked for 'squad', '스쿼드')")
                    
                if order_col:
                    st.success(f"✅ Found Order Column: `{order_col}`")
                else:
                    st.warning("⚠️ Order Column NOT FOUND (looked for 'order', '순서', '정렬')")
                    
        else:
            st.error(f"❌ Target GID `{TARGET_GID}` not found in this spreadsheet.")

    except gspread.SpreadsheetNotFound:
        st.error("❌ Spreadsheet NOT found. Check the ID.")
    except Exception as e:
        st.error(f"❌ Error opening/reading sheet: {e}")
        st.exception(e)

except Exception as e:
    st.error(f"❌ Fatal Error: {e}")
