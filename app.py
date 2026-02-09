import streamlit as st
import pandas as pd
from views import roadmap, analysis, data_ops
from logic import process_data, apply_sorting, filter_data
from gsheet_handler import load_data
from squad_manager import sort_squads
import utils

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

# -----------------------------------------------------------------------------
# DATA CONNECTION SETTINGS
# -----------------------------------------------------------------------------
with st.sidebar.expander("🔌 Connection Settings", expanded=False):
    # --- Roadmap Data Settings ---
    st.markdown("### 📌 Roadmap Data")
    default_id = st.secrets.get("G_SHEET_ID", "")
    default_gid = st.secrets.get("G_SHEET_GID", "")
    
    sheet_id = st.text_input("GSheet ID", value=default_id, key="roadmap_id")
    worksheet_name = st.text_input("Worksheet Name / GID", value=default_gid, key="roadmap_gid")
    
    st.divider()

    # --- Resource Data Settings ---
    st.markdown("### 👥 Resource Data")
    res_source = st.radio("Source", ["Google Sheet", "File Upload"], horizontal=True, key="res_source_radio")
    
    if res_source == "Google Sheet":
        default_res_id = st.secrets.get("RES_SHEET_ID", "")
        default_res_gid = st.secrets.get("RES_SHEET_GID", "")
        
        res_sheet_id = st.text_input("GSheet ID (Resource)", value=default_res_id, key="res_id")
        res_sheet_gid = st.text_input("GSheet GID (Resource)", value=default_res_gid, key="res_gid")
        
        load_res_btn = st.button("Load Resource Data", key="load_res_btn")
    else:
        resource_file = st.file_uploader("Upload Resource File", type=['xlsx', 'xls'], key="res_file")

# -----------------------------------------------------------------------------
# LOAD DATA LOGIC
# -----------------------------------------------------------------------------

# 1. Load Roadmap Data
df = None
raw_df = None
if sheet_id:
    with st.spinner("Loading Roadmap data..."):
        # load_data caches? If not, this might re-run on every interaction. 
        # gsheet_handler.load_data should ideally be cached or st.cache_data used.
        # For now, we follow existing pattern.
        raw_df = load_data(sheet_id, worksheet_name)
        if not raw_df.empty:
            df = process_data(raw_df.copy()) # Use copy to preserve raw_df
        else:
            st.sidebar.warning("Roadmap 데이터를 불러오지 못했습니다.")

# Fallback: Roadmap File Uploader (only if no sheet loaded)
if df is None:
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("또는 Roadmap 엑셀 업로드", type=['xlsx', 'xls'], key="roadmap_file")
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        df = process_data(df)

# 2. Load Resource Data
df_resource = None

if res_source == "File Upload" and resource_file:
    df_resource = utils.load_resource_data(resource_file)

elif res_source == "Google Sheet":
    # Auto-load if ID is present (uses cached load_data)
    if res_sheet_id:
        try:
            raw_res_df = load_data(res_sheet_id, res_sheet_gid)
            if not raw_res_df.empty:
                df_resource = utils.process_resource_dataframe(raw_res_df)
                # if df_resource is not None:
                #      st.sidebar.success("Resource Data Loaded!")
            else:
                 pass
        except Exception as e:
            st.sidebar.error(f"Error: {e}")



# -----------------------------------------------------------------------------
# MAIN CONTENT & SIDEBAR LOGIC
# -----------------------------------------------------------------------------

if page == "Roadmap View":
    st.title("🗺️ Roadmap View")
    # Roadmap has its own sidebar filters, so we bypass the global filter block
    # and pass the raw processed DF (df) instead of final_df
    if df is not None:
        roadmap.render_roadmap(df)
    else:
        st.info("데이터를 연결해주세요 (Google Sheet ID 또는 파일 업로드)")

else:
    # -------------------------------------------------------------------------
    # GLOBAL FILTERS (For Analysis & Data Ops)
    # -------------------------------------------------------------------------
    st.sidebar.subheader("🔍 Filters")
    
    if df is not None:
        # Status Filter
        all_statuses = list(df['Status'].unique()) if 'Status' in df.columns else []
        selected_status = st.sidebar.multiselect("Status", all_statuses, default=all_statuses)
        
        # Squad Filter
        all_squads = list(df['Squad'].unique()) if 'Squad' in df.columns else []
        all_squads = sort_squads(all_squads) # Apply custom sort order
        selected_squads = st.sidebar.multiselect("Squad", all_squads, default=all_squads)
        
        # Date Range Filter removed as per user request
        date_range = None

        # Sorting options
        st.sidebar.subheader("🔃 Sorting")
        sort_options = [c for c in df.columns if c not in ['Start', 'End', 'Duration_Text']]
        user_sort_col = st.sidebar.selectbox("Custom Sort Column", ["None"] + sort_options)
        
        # Apply Logic
        filtered_df = filter_data(df, selected_status, selected_squads, date_range)
        
        # Apply Sorting (Only meaningful for Roadmap usually, but good for table view too)
        final_df = apply_sorting(filtered_df, user_sort_col if user_sort_col != "None" else None)
        
        st.sidebar.info(f"Total Tasks: {len(final_df)}")
        
        if page == "Analysis Report":
            st.title("📊 Analysis Report")
            # if resource_file: logic removed as it is handled above.
            analysis.render_analysis_report(final_df, df_resource)

        elif page == "Data Ops":
            st.title("🛠 Data Editor")
            # For Data Ops, we show the RAW data (raw_df) to prevent data loss and show original columns/order.
            if raw_df is not None:
                data_ops.render_data_ops(raw_df, sheet_id, worksheet_name)
            else:
                 st.info("데이터를 연결해주세요 (Google Sheet ID 또는 파일 업로드)")

    else:
        st.info("데이터를 연결해주세요 (Google Sheet ID 또는 파일 업로드)")
