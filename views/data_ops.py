import streamlit as st
import pandas as pd
from gsheet_handler import save_snapshot

def render_data_ops(df: pd.DataFrame, sheet_url_or_id, worksheet_name):
    # st.header("🛠 데이터 운영 (Data Ops)") # Title handled in app.py
    st.info("""
    데이터를 직접 수정하고 저장할 수 있습니다. 저장 시 원본 구글 시트에 내용이 덮어씌워집니다.
    
    :red[**⚠️ 주의: 필터링 여부와 관계없이 전체 데이터가 불러와집니다.**]
    (데이터 유실 방지를 위해, Data Ops에서는 필터가 적용되지 않은 전체 데이터를 수정하게 됩니다.)

    ---
    :gray[**※ 데이터 정렬 기준**]
    
    :gray[**1. 사용자 지정 정렬** (Custom Sort Column)]
    :gray[   - 사이드바에서 특정 컬럼을 선택했다면 해당 컬럼이 최우선으로 정렬됩니다.]
    
    :gray[**2. 스쿼드** (Squad)]
    :gray[   - `[MASTER]Squad order.xlsx` 파일(또는 코드 내 고정 순서)에 정의된 순서대로 정렬됩니다.]
    
    :gray[**3. 정렬 순서** (Order)] 
    :gray[   - 원본 데이터에 있는 `No` 또는 `Order` 컬럼의 숫자 순서대로 정렬됩니다.]
    """)
    
    
    # Initialize session state for data editor key if not exists
    if "data_ops_key" not in st.session_state:
        st.session_state.data_ops_key = 0

    # Refresh Button
    if st.button("🔄 데이터 새로고침 (Refresh Data)"):
        st.cache_data.clear()
        st.session_state.data_ops_key += 1 # Increment key to force reset
        st.rerun()

    # Data Editor
    # Use dynamic key to allow resetting state
    editor_key = f"data_editor_{st.session_state.data_ops_key}"
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=editor_key)
    
    if st.button("변경 사항 저장 (Save Snapshot)", type="primary"):
        with st.spinner("저장 중..."):
            success = save_snapshot(sheet_url_or_id, edited_df, worksheet_name)
            if success:
                st.success("저장 완료! 원본 시트가 업데이트되었습니다.")
                st.rerun()
            else:
                st.error("저장에 실패했습니다. 설정을 확인해주세요.")
