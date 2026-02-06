import streamlit as st
import pandas as pd
from gsheet_handler import save_snapshot

def render_data_ops(df: pd.DataFrame, sheet_url_or_id):
    st.header("🛠 데이터 운영 (Data Ops)")
    st.info("데이터를 직접 수정하고 저장할 수 있습니다. 저장 시 구글 시트에 새로운 스냅샷이 생성됩니다.")
    
    # Data Editor
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("변경 사항 저장 (Save Snapshot)", type="primary"):
        with st.spinner("저장 중..."):
            success = save_snapshot(sheet_url_or_id, edited_df)
            if success:
                st.success("저장 완료! 새로운 스냅샷이 생성되었습니다.")
                st.rerun()
            else:
                st.error("저장에 실패했습니다. 설정을 확인해주세요.")
