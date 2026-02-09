import streamlit as st
import pandas as pd
from gsheet_handler import save_snapshot

def render_data_ops(df: pd.DataFrame, sheet_url_or_id):
    # st.header("🛠 데이터 운영 (Data Ops)") # Title handled in app.py
    st.info("""
    데이터를 직접 수정하고 저장할 수 있습니다. 저장 시 구글 시트에 새로운 스냅샷이 생성됩니다.
    
    ---
    :gray[**※ 데이터 정렬 기준**]
    
    :gray[**1. 사용자 지정 정렬** (Custom Sort Column)]
    :gray[   - 사이드바에서 특정 컬럼을 선택했다면 해당 컬럼이 최우선으로 정렬됩니다.]
    
    :gray[**2. 스쿼드** (Squad)]
    :gray[   - `[MASTER]Squad order.xlsx` 파일(또는 코드 내 고정 순서)에 정의된 순서대로 정렬됩니다.]
    
    :gray[**3. 정렬 순서** (Order)] 
    :gray[   - 원본 데이터에 있는 `No` 또는 `Order` 컬럼의 숫자 순서대로 정렬됩니다.]
    """)
    
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
