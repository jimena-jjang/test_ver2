
import streamlit as st
import pandas as pd
import utils
import gsheet_handler
import os

st.title("🐞 Squad Order Verification")

st.write("Checking where the squad order is coming from...")

# 1. Check Google Sheet Direct Load
st.subheader("1. Testing `gsheet_handler.load_squad_order_from_sheet` directly")
SHEET_ID = '1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts'
GID = '2103927428'

try:
    with st.spinner("Connecting to Google Sheet..."):
        # Clear cache to force fresh load
        gsheet_handler.load_squad_order_from_sheet.clear()
        
        sheet_order = gsheet_handler.load_squad_order_from_sheet(SHEET_ID, GID)
        
    if sheet_order:
        st.success(f"✅ Successfully loaded {len(sheet_order)} squads from Google Sheet.")
        st.write("First 10 items:", sheet_order[:10])
        st.write("Full List:", sheet_order)
    else:
        st.error("❌ Failed to load from Google Sheet. Returned empty list.")
        
except Exception as e:
    st.error(f"❌ Exception occurred: {e}")

st.divider()

# 2. Check Utils Logic (Precedence)
st.subheader("2. Testing `utils.get_custom_squad_order()`")
st.write("This function determines what the Roadmap view actually uses.")

try:
    final_order = utils.get_custom_squad_order()
    
    if final_order:
        st.info(f"📋 Utils returned {len(final_order)} squads.")
        st.write("items:", final_order)
        
        # Comparison with Sheet Order
        if sheet_order and final_order == sheet_order:
             st.success("✅ `utils.get_custom_squad_order` is correctly using the Google Sheet data.")
        elif sheet_order:
             st.warning("⚠️ Mismatch! `utils` is NOT returning the Google Sheet data. It might be falling back to a local file.")
             st.write("Sheet Order:", sheet_order[:5])
             st.write("Utils Order:", final_order[:5])
        else:
             st.warning("⚠️ Google Sheet load failed, so Utils returned something else (Fallback).")
    else:
        st.warning("⚠️ `utils.get_custom_squad_order` returned None or empty list.")

except Exception as e:
    st.error(f"❌ Exception in utils: {e}")

st.divider()

# 3. Check Local Fallback Files
st.subheader("3. Checking Local Fallback Files")
master_file = '[master]squad order.xlsx'
if os.path.exists(master_file):
    st.write(f"Found local file: `{master_file}`")
else:
    st.write(f"Local file `{master_file}` NOT found.")

