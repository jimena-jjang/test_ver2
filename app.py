import streamlit as st
import pandas as pd
from views import roadmap, analysis, data_ops
from logic import process_data, apply_sorting, filter_data
from gsheet_handler import load_data

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Product Management System",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.title("🗓️ PMS (Ver.2)")

# Navigation
page = st.sidebar.radio("Navigation", ["Roadmap View", "Analysis Report", "Data Ops"])

st.sidebar.divider()

# Data Connection Settings (Mock or Secret)
# For demo, allow users to input Sheet ID if not in secrets
sheet_id = st.sidebar.text_input("Google Sheet ID", value=st.secrets.get("G_SHEET_ID", ""))
worksheet_name = st.sidebar.text_input("Worksheet Name", value="Sheet1")

# Load Data
df = None
if sheet_id:
    with st.spinner("Loading data..."):
        raw_df = load_data(sheet_id, worksheet_name)
        if not raw_df.empty:
            df = process_data(raw_df)
        else:
            st.sidebar.error("데이터 로드 실패")

# Fallback: File Uploader if no sheet connected
if df is None:
    uploaded_file = st.sidebar.file_uploader("또는 엑셀 파일 업로드", type=['xlsx', 'xls'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df = process_data(df)

# Global Filters (Apply to all views usually, or just Roadmap)
st.sidebar.subheader("🔍 Filters")

if df is not None:
    # Status Filter
    all_statuses = list(df['Status'].unique()) if 'Status' in df.columns else []
    selected_status = st.sidebar.multiselect("Status", all_statuses, default=all_statuses)
    
    # Squad Filter
    all_squads = list(df['Squad'].unique()) if 'Squad' in df.columns else []
    selected_squads = st.sidebar.multiselect("Squad", all_squads, default=all_squads)
    
    # Date Range
    min_date = df['Start'].min() if 'Start' in df.columns and not df['Start'].isnull().all() else None
    max_date = df['End'].max() if 'End' in df.columns and not df['End'].isnull().all() else None
    
    date_range = None
    if min_date and max_date:
        date_range = st.sidebar.date_input("Period", [min_date, max_date])

    # Sorting options
    st.sidebar.subheader("🔃 Sorting")
    sort_options = [c for c in df.columns if c not in ['Start', 'End', 'Duration_Text']]
    user_sort_col = st.sidebar.selectbox("Custom Sort Column", ["None"] + sort_options)
    
    # Apply Logic
    filtered_df = filter_data(df, selected_status, selected_squads, date_range)
    
    # Apply Sorting (Only meaningful for Roadmap usually, but good for table view too)
    final_df = apply_sorting(filtered_df, user_sort_col if user_sort_col != "None" else None)
    
    st.sidebar.info(f"Total Tasks: {len(final_df)}")

else:
    st.info("데이터를 연결해주세요 (Google Sheet ID 또는 파일 업로드)")
    st.stop()

# -----------------------------------------------------------------------------
# MAIN CONTENT
# -----------------------------------------------------------------------------

if page == "Roadmap View":
    st.title("🗺️ Roadmap View")
    roadmap.render_roadmap(final_df)

elif page == "Analysis Report":
    st.title("📊 Analysis Report")
    analysis.render_analysis_report(final_df)

elif page == "Data Ops":
    st.title("🛠 Data Editor")
    # For Data Ops, we might want to show the RAW data or at least allow editing the filtered subset
    # Typically editing is safer on the whole dataset or clearly marked.
    # We will pass the processed DF but edits need to map back conceptually.
    # Here we just pass the filtered view for editing, but note that saving might need careful handling if rows are hidden.
    # The requirement says "Data Editor". We'll just pass final_df.
    data_ops.render_data_ops(final_df, sheet_id)
