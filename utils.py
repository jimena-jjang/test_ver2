import pandas as pd
import streamlit as st
import textwrap
import os
import unicodedata
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 상수 및 스타일 정의
# -----------------------------------------------------------------------------
STATUS_CONFIG = {
    '진행 완료': {
        'border': '#10B981', 'fill': '#10B981', 'style': 'solid', 'icon': '✅', 'text_color': '#047857', 'bg_color': '#ECFDF5' # Green
    },
    '진행 중': {
        'border': '#3B82F6', 'fill': '#3B82F6', 'style': 'solid', 'icon': '🏃', 'text_color': '#1D4ED8', 'bg_color': '#EFF6FF' # Blue
    },
    '진행 예정': {
        'border': '#8B5CF6', 'fill': '#8B5CF6', 'style': 'solid', 'icon': '🗓️', 'text_color': '#6D28D9', 'bg_color': '#F5F3FF' # Purple
    },
    '이슈': {
        'border': '#EF4444', 'fill': 'rgba(239, 68, 68, 0.7)', 'style': 'dashed', 'icon': '🚨', 'text_color': '#B91C1C', 'bg_color': '#FEF2F2' # Red
    },
    '보류': {
        'border': '#F59E0B', 'fill': '#F59E0B', 'style': 'dashed', 'icon': '⏸️', 'text_color': '#B45309', 'bg_color': '#FFFBEB' # Amber
    },
    '미정': {
        'border': '#9CA3AF', 'fill': '#9CA3AF', 'style': 'dashed', 'icon': '❓', 'text_color': '#4B5563', 'bg_color': '#F3F4F6' # Gray
    },
    '단순 인입': {
        'border': '#64748B', 'fill': '#64748B', 'style': 'dashed', 'icon': '📥', 'text_color': '#334155', 'bg_color': '#F1F5F9' # Slate
    },
    'DROP': {
        'border': '#1F2937', 'fill': '#1F2937', 'style': 'dashed', 'icon': '⛔', 'text_color': '#111827', 'bg_color': '#F3F4F6' # Dark Gray
    }
}

# Helper to get config safely
def get_status_style(status):
    if not isinstance(status, str):
        return {
        'border': '#888888', 'fill': 'white', 'style': 'solid', 'icon': ''
    }
    
    
    # Normalization and stripping
    clean_status = unicodedata.normalize('NFC', status).strip()
    
    if clean_status in STATUS_CONFIG:
        return STATUS_CONFIG[clean_status]
        
    # Dynamic styling for unknown statuses
    # Use hash to pick a fallback color consistently
    color = FALLBACK_COLORS[hash(clean_status) % len(FALLBACK_COLORS)]
    return {
        'border': color, 'fill': color, 'style': 'solid', 'icon': '', 'text_color': 'white'
    }

STATUS_COLORS = {k: v['border'] for k, v in STATUS_CONFIG.items()} # Backwards compatibility just in case

SQUAD_COLORS = {
    '회원': '#2C3E50',           # Dark Navy
    '커머스': '#8E44AD',         # Deep Purple
    '팬덤': '#2980B9',           # Trust Blue
    'APP': '#27AE60',            # Fresh Green
    '내부과제': '#7F8C8D',       # Calm Gray
    'devops': '#7F8C8D',         # Calm Gray
    '전사공통': '#34495E',       # Dark Blue Gray
}

FALLBACK_COLORS = ['#E67E22', '#D35400', '#C0392B', '#16A085', '#2C3E50']
DEFAULT_STATUS_COLOR = '#888888'

# -----------------------------------------------------------------------------
# 헬퍼 함수 정의
# -----------------------------------------------------------------------------

def get_status_color(status):
    """상태에 따른 색상을 반환 (동적 처리)"""
    if status in STATUS_COLORS:
        return STATUS_COLORS[status]
    # 미리 정의되지 않은 상태는 해시 기반으로 색상 할당
    return FALLBACK_COLORS[hash(status) % len(FALLBACK_COLORS)]

def get_visual_width(text):
    """
    Calculate visual width of text.
    East Asian Width 'W', 'F', 'A' count as 2, others as 1.
    """
    width = 0
    for char in str(text):
        if unicodedata.east_asian_width(char) in ['F', 'W', 'A']:
            width += 2
        else:
            width += 1
    return width

def wrap_text_by_pixels(text, max_px, font_size=12):
    """
    Wraps text ensuring each line does not exceed max_px.
    Assumes:
    - Wide char (Korean/CJK): ~1.8 * font_size (Safe for Arial Black/Bold)
    - Narrow char (English/Num): ~0.95 * font_size
    """
    if not text: return ""
    
    str_text = str(text)
    lines = []
    current_line = []
    current_px = 0
    
    # Constants for pixel estimation (Dynamic based on font size)
    # Arial Black is very wide, so we use conservative multipliers
    # INCREASED multipliers to force wrapping (V4 fix was insufficient)
    PX_WIDE = int(font_size * 2.2)   
    PX_NARROW = int(font_size * 1.2) 
    
    for char in str_text:
        # Determine char width
        is_wide = unicodedata.east_asian_width(char) in ['F', 'W', 'A']
        char_px = PX_WIDE if is_wide else PX_NARROW
        
        # Check if adding char exceeds max_px
        if current_px + char_px > max_px:
            # Push current line and start new
            if current_line:
                lines.append("".join(current_line))
            current_line = [char]
            current_px = char_px
        else:
            current_line.append(char)
            current_px += char_px
            
    if current_line:
        lines.append("".join(current_line))
        
    return "<br>".join(lines)

def wrap_text_html(text, width=40):
    if not text: return ""
    # Fallback to character count based wrapping if needed, but prefer usage of wrap_text_by_pixels
    return "<br>".join(textwrap.wrap(str(text), width=width))

def get_custom_squad_order():
    """Squad 정렬 순서를 가져옵니다. 
    1순위: [master]squad order.xlsx (정렬 순서 컬럼 이용)
    2순위: Squad 정렬순서.xlsx (파일 내 등장 순서)
    """
    try:
        # 0. [New] Google Sheet Order (Priority 1)
        from gsheet_handler import load_squad_order_from_sheet
        SHEET_ID = '1XwHp_Lm7FQEmZzib8qJ1C1Q--ogCTKPXcHYhMlkE-Ts'
        GID = '2103927428'
        
        sheet_order = load_squad_order_from_sheet(SHEET_ID, GID)
        if sheet_order:
            print(f"DEBUG: Loaded {len(sheet_order)} squads from Sheet.")
            return sheet_order
        else:
            print("DEBUG: Google Sheet returned empty squad order.")

        # 1. [master]squad order.xlsx 확인 (Fallback)
        master_file = '[master]squad order.xlsx'
        if os.path.exists(master_file):
            df_master = pd.read_excel(master_file)
            df_master.columns = df_master.columns.astype(str).str.strip()
            
            if 'Squad (대분류)' in df_master.columns and '정렬 순서' in df_master.columns:
                # 정렬 순서기준 오름차순 정렬
                df_master['정렬 순서'] = pd.to_numeric(df_master['정렬 순서'], errors='coerce').fillna(999)
                df_master = df_master.sort_values(by='정렬 순서', ascending=True)
                return df_master['Squad (대분류)'].dropna().unique().tolist()

        # 2. (Fallback) Squad 정렬순서.xlsx 확인 (기존 로직)
        # 파일명 매칭 (자소 분리 문제 해결을 위해 포함 여부 확인)
        target_files = [f for f in os.listdir('.') if 'Squad' in unicodedata.normalize('NFC', f) and '정렬' in unicodedata.normalize('NFC', f) and f.endswith('.xlsx')]
        
        if target_files:
            sort_file = target_files[0]
            df_sort = pd.read_excel(sort_file)
            df_sort.columns = df_sort.columns.astype(str).str.strip()
            if 'Squad (대분류)' in df_sort.columns:
                return df_sort['Squad (대분류)'].dropna().unique().tolist()
            
    except Exception as e:
        print(f"정렬 파일 로드 실패: {e}") 
        
    return None

def load_and_process_data(file):
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.astype(str).str.strip()
        
        col_map = {
            'Squad (대분류)': 'Squad',
            '1depth_name (중분류)': 'Project', # User requested Project column
            '1depth_name': 'Project',
            'Goal (목표)': 'Goal',
            'Subproject_Name (소분류)': 'Task',
            '시작일 (Start)': 'Start',
            '종료일 (End)': 'End',
            '상태 (Status)': 'Status',
            'Type (유형)': 'Type',
            # New Mappings requested by User
            'squad': 'Squad',
            'type': 'Type', 
            'subproject_name': 'Task', 
            'project_name': 'Project',
            'Project_Name': 'Project',
            'Project': 'Project', # Exact match
            'start_date': 'Start',
            'end_date': 'End',
            'status': 'Status',
            '타겟 일정(표기용)': 'Display_Date',
            '진행 기간 (일/주)': 'Duration_Text',
            '코멘트 (Comment)': 'Comment',
            'comment': 'Comment',
            'Comment': 'Comment',
            '비고': 'Comment',
            '설명': 'Comment'
        }
        
        rename_dict = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # Normalize Status values to prevent grouping issues
        if 'Status' in df.columns:
             # Handle multiple Status columns if faulty merge (take first)
            if isinstance(df['Status'], pd.DataFrame):
                 df['Status'] = df['Status'].iloc[:, 0]
            df['Status'] = df['Status'].astype(str).apply(lambda x: unicodedata.normalize('NFC', x).strip())
        
        required = ['Squad', 'Task', 'Start', 'End', 'Status']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"필수 컬럼이 누락되었습니다: {missing}")
            return None

        # 필수 컬럼 중 'Task'가 없는 경우만 드롭 (날짜는 비어있어도 허용)
        df = df.dropna(subset=['Task'])
        
        # 날짜 변환 (에러 발생 시 NaT 처리)
        df['Start'] = pd.to_datetime(df['Start'], errors='coerce')
        df['End'] = pd.to_datetime(df['End'], errors='coerce')
        
        string_cols = ['Status', 'Type', 'Squad', 'Task', 'Group', 'Project']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Task가 빈 문자열인 경우 제거 (Ghost Rows 방지)
        df = df[df['Task'] != '']
        df = df[df['Task'] != 'nan'] # 문자열 'nan' 처리
        
        # Squad가 없거나 nan인 경우 제거
        df = df[df['Squad'] != '']
        df = df[df['Squad'] != 'nan']

        for col in ['Display_Date', 'Duration_Text', 'Comment']:
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].fillna('')
        
        # if 'Group' not in df.columns:
        #     df['Group'] = df['Squad']
            
        if 'Type' not in df.columns:
            df['Type'] = 'Task'
        else:
            df['Type'] = df['Type'].fillna('Task')
        df['Status'] = df['Status'].fillna('진행 예정')
        
        # Status 정렬 로직 (진행중 > 진행예정 > 진행완료 > 미정 > Drop)
        status_priority = ['진행 중', '진행 예정', '진행 완료', '미정', '이슈', 'DROP', '단순 인입']
        # Normalize priority list
        status_priority = [unicodedata.normalize('NFC', s) for s in status_priority]
        
        present_status = df['Status'].unique().tolist()
        final_status_order = [s for s in status_priority if s in present_status]
        others_status = [s for s in present_status if s not in final_status_order]
        final_status_order.extend(others_status)
        
        df['Status'] = pd.Categorical(df['Status'], categories=final_status_order, ordered=True)
        
        # Squad 정렬 로직
        custom_order = get_custom_squad_order()
        
        if custom_order:
            # 데이터에 있는 Squad 목록 (등장 순서대로)
            present_squads = df['Squad'].unique().tolist()
            
            # 1. Custom Order에 정의된 것들을 먼저 배치 (순서 유지)
            final_order = [s for s in custom_order if s in present_squads]
            
            # 2. 정의되지 않은 것들은 뒤에 배치 (등장 순서 유지)
            others = [s for s in present_squads if s not in final_order]
            final_order.extend(others)
            
            # [User Request] Ensure '공통' is always first if present
            squad_common = next((s for s in final_order if '공통' in unicodedata.normalize('NFC', str(s))), None)
            if squad_common:
                final_order.remove(squad_common)
                final_order.insert(0, squad_common)
            
            df['Squad'] = pd.Categorical(df['Squad'], categories=final_order, ordered=True)
            
        else:
            # 파일이 없거나 로드 실패 시: 원래 파일의 등장 순서 유지
            original_squad_order = df['Squad'].unique().tolist()
            
            # [User Request] Ensure '공통' is always first even in default order
            squad_common = next((s for s in original_squad_order if '공통' in unicodedata.normalize('NFC', str(s))), None)
            if squad_common:
                original_squad_order.remove(squad_common)
                original_squad_order.insert(0, squad_common)
                
            df['Squad'] = pd.Categorical(df['Squad'], categories=original_squad_order, ordered=True)
        
        # 정렬: Squad -> Goal -> Group -> Start
        sort_cols = ['Squad', 'Goal', 'Group', 'Start']
        # Goal이 없는 경우 대비 (혹시 모를 에러 방지)
        available_sort_cols = [c for c in sort_cols if c in df.columns]
        
        df = df.sort_values(by=available_sort_cols, ascending=[True] * len(available_sort_cols))
        
        # Categorical type preserved for sorting
        # df['Squad'] = df['Squad'].astype(str) # Removed to keep order
        
        return df
    
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return None

    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return None

def process_resource_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates and processes the resource DataFrame.
    Expects columns related to 'Squad' and 'Headcount'.
    """
    try:
        df.columns = df.columns.astype(str).str.strip()
        
        # 1. Normalize Squad Column
        target_squad_col = None
        for col in df.columns:
            if col.strip().lower() == 'squad':
                target_squad_col = col
                break
        
        if target_squad_col:
            df = df.rename(columns={target_squad_col: 'Squad'})
        elif 'Squad (대분류)' in df.columns:
             df = df.rename(columns={'Squad (대분류)': 'Squad'})
             
        if 'Squad' not in df.columns:
            st.error(f"리소스 데이터에 'Squad' 컬럼이 없습니다. (현재 컬럼: {list(df.columns)})")
            return None
            
        # 2. Find Headcount and Min_Personnel Columns
        headcount_col = None
        min_personnel_col = None
        
        for col in df.columns:
            if '보유' in col and '인원' in col:
                headcount_col = col
            if '최소' in col and '투입' in col:
                min_personnel_col = col
                
        if not headcount_col:
            # Check for English headers just in case
            if 'Headcount' in df.columns:
                headcount_col = 'Headcount'
            else:
                st.error("리소스 데이터에 '보유 인원' 관련 컬럼이 없습니다. (예: 보유 인원)")
                return None
            
        # 3. Select and Rename
        cols_to_use = ['Squad', headcount_col]
        rename_map = {headcount_col: 'Headcount'}
        
        if min_personnel_col:
            cols_to_use.append(min_personnel_col)
            rename_map[min_personnel_col] = 'Min_Personnel'
        elif 'Min_Personnel' in df.columns:
            cols_to_use.append('Min_Personnel')
            
        df = df[cols_to_use].copy()
        df = df.rename(columns=rename_map)
        
        if 'Squad' in df.columns:
            df['Squad'] = df['Squad'].astype(str).str.strip().apply(lambda x: unicodedata.normalize('NFC', x))
        
        # 4. Data Cleaning
        df['Headcount'] = pd.to_numeric(df['Headcount'], errors='coerce').fillna(0)
        
        if 'Min_Personnel' in df:
            df['Min_Personnel'] = pd.to_numeric(df['Min_Personnel'], errors='coerce').fillna(1.0)
        else:
            df['Min_Personnel'] = 1.0
        
        return df
        
    except Exception as e:
        st.error(f"리소스 데이터 처리 중 오류 발생: {e}")
        return None

def load_resource_data(file):
    """리소스(인원) 엑셀 파일 로드 Function"""
    try:
        df = pd.read_excel(file)
        return process_resource_dataframe(df)
    except Exception as e:
        st.error(f"리소스 파일 읽기 중 오류 발생: {e}")
        return None

