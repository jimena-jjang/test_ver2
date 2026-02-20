import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
import plotly.express as px
from squad_manager import get_squad_order

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
STATUS_CONFIG = {
    '진행 완료': {'color': '#10B981'},
    '진행 중': {'color': '#3B82F6'},
    '진행 예정': {'color': '#8B5CF6'},
    '이슈': {'color': '#EF4444'},
    '단순 인입': {'color': '#64748B'},
    'DROP': {'color': '#1F2937'},
}

STATUS_ORDER = [
    '진행 중',
    '진행 예정',
    '이슈',
    '단순 인입',
    '진행 완료',
    'DROP'
]

DEFAULT_STATUS_COLOR = '#888888'

# -----------------------------------------------------------------------------
# DATA PROCESSING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names and formats data.
    """
    df.columns = df.columns.astype(str).str.strip()
    
    # Column mapping based on requirements and existing utils.py
    # Column mapping based on requirements and existing utils.py
    col_map = {
        'Squad (대분류)': 'Squad', 'squad': 'Squad',
        'subproject_name': 'Task', 'Subproject_Name (소분류)': 'Task',
        'start_date': 'Start', '시작일 (Start)': 'Start',
        'end_date': 'End', '종료일 (End)': 'End',
        'status': 'Status', '상태 (Status)': 'Status',
        'Goal (목표)': 'Goal', 'goal': 'Goal',
        'order': 'Order', '정렬 순서': 'Order',
        
        # New columns from [Master] CTO office Roadmap (2).xlsx
        'Biz_impact': 'Biz_impact', 'main_goal': 'Biz_impact', 'Main_Goal': 'Biz_impact',
        'Product_track': 'Product_track', 'sub_goal': 'Product_track', 'Sub_Goal': 'Product_track',
        
        'project_name': 'Project',
        'type': 'Type',
        'comment': 'Comment', 
        'target': 'Target',
        'cto_manager': 'Manager',
        'PM': 'PM', 'PD': 'PD', 'FE': 'FE', 'BE': 'BE', 'QA': 'QA',
        'remarks': 'Remarks'
    }
    
    rename_dict = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
    # Handle Goal column logic
    if 'Product_track' in df.columns and 'Goal' not in df.columns:
        df['Goal'] = df['Product_track']
    
    # Normalize strings
    string_cols = ['Squad', 'Task', 'Status', 'Goal', 'Biz_impact', 'Product_track', 'Project', 'Type', 'Comment', 'Target', 'Manager', 'PM', 'PD', 'FE', 'BE', 'QA', 'Remarks']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().apply(lambda x: unicodedata.normalize('NFC', x) if isinstance(x, str) else x)

    # Date conversion
    for col in ['Start', 'End']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Ensure required columns exist
    required_cols = ['Squad', 'Task', 'Start', 'End', 'Status']
    for col in required_cols:
        if col not in df.columns:
            # Handle missing gracefully for partial data; but for critical logic, we might need to warn.
            # For now, create empty or default.
            if col == 'Status':
                df['Status'] = '진행 예정'
            else:
                pass # Let it fail or handle downstream if critical

    # Sort Status by defined order
    # Create final order: STATUS_ORDER candidates first, then any others found in data sorted alphabetically
    present_status = df['Status'].unique().tolist() if 'Status' in df.columns else []
    
    # Identify statuses not in our fixed list
    known_set = set(STATUS_ORDER)
    unknown_statuses = sorted([s for s in present_status if s not in known_set])
    
    # Final combined order
    final_status_order = STATUS_ORDER + unknown_statuses
    
    # Apply Categorical type
    df['Status'] = pd.Categorical(df['Status'], categories=final_status_order, ordered=True)

    return df

def apply_sorting(df: pd.DataFrame, user_sort_col: str = None) -> pd.DataFrame:
    """
    Applies the complex sorting logic:
    1. User selected column (optional)
    2. Squad (using predefined order if possible)
    3. Order (DB defined column)
    """
    sort_cols = []
    ascending = []
    
    if user_sort_col and user_sort_col in df.columns:
        sort_cols.append(user_sort_col)
        ascending.append(True)
        
    if 'Squad' in df.columns:
        # Create a categorical type for Squad to enforce custom order
        present_squads = df['Squad'].unique()
        
        # Load dynamic order
        squad_order_list = get_squad_order()
        
        ordered_squads = [s for s in squad_order_list if s in present_squads]
        others = [s for s in present_squads if s not in ordered_squads]
        final_squad_order = ordered_squads + sorted(others)
        
        df['Squad'] = pd.Categorical(df['Squad'], categories=final_squad_order, ordered=True)
        sort_cols.append('Squad')
        ascending.append(True)
        
    if 'Order' in df.columns:
        # Convert to numeric if possible
        df['Order'] = pd.to_numeric(df['Order'], errors='coerce').fillna(9999)
        sort_cols.append('Order')
        ascending.append(True)
        
    if not sort_cols:
        return df

    return df.sort_values(by=sort_cols, ascending=ascending)

# -----------------------------------------------------------------------------
# FILTERING
# -----------------------------------------------------------------------------
def filter_data(df: pd.DataFrame, status_filter=None, squad_filter=None, date_range=None) -> pd.DataFrame:
    filtered = df.copy()
    
    if status_filter:
        filtered = filtered[filtered['Status'].isin(status_filter)]
        
    if squad_filter:
        filtered = filtered[filtered['Squad'].isin(squad_filter)]
        
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        # Overlap logic: (Start <= RangeEnd) AND (End >= RangeStart)
        mask = (filtered['Start'] <= end_date) & (filtered['End'] >= start_date)
        # Or simple existing within range logic depending on requirement. 
        # "Specific period (count tasks within period)" usually means active in that period.
        filtered = filtered[mask]
        
    return filtered

# -----------------------------------------------------------------------------
# ANALYSIS
# -----------------------------------------------------------------------------
def calculate_workload(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes workload per Squad.
    """
    if df.empty:
        return pd.DataFrame()
        
    workload = df.groupby('Squad').agg(
        Total_Tasks=('Task', 'count'),
        Active_Tasks=('Status', lambda x: x.isin(['진행 중', '진행 예정']).sum())
    ).reset_index()
    return workload

def predict_start_date(df: pd.DataFrame, squad: str) -> datetime:
    """
    Predicts the earliest start date for a new task in a squad
    by finding the latest end date of current tasks.
    """
    squad_tasks = df[df['Squad'] == squad]
    if squad_tasks.empty:
        return datetime.today()
    
    max_end = squad_tasks['End'].max()
    if pd.isna(max_end):
        return datetime.today()
        
    # Start next day
    return max_end + pd.Timedelta(days=1)


def identify_issues(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns tasks that are defined as issues or strategic tasks.
    Prioritizes '보류/이슈' Status first, then '전략과제'.
    """
    # 1. Status Issue
    status_issues = df[df['Status'] == '이슈'].copy()
    status_issues['Issue_Type'] = 'Status Issue'
    
    # 2. Strategic Tasks (Only if Status == '단순 인입')
    strategic_tasks = pd.DataFrame()
    if 'Biz_impact' in df.columns:
        is_strategic = df['Biz_impact'].astype(str).str.contains('전략과제', na=False)
        is_simple = df['Status'] == '단순 인입'
        
        strategic_mask = is_strategic & is_simple
        strategic_tasks = df[strategic_mask].copy()
        strategic_tasks['Issue_Type'] = 'Strategic Task'

    # Combine
    # Note: If a task is both, it appears in both dfs. 
    # But '이슈' status tasks are already captured in status_issues.
    # The strategic_tasks df only has '단순 인입' status, so no overlap with '이슈' status.
    # We can safely concat or use mask union.
    
    # Mask 1: Status Issue
    mask_status = df['Status'] == '이슈'
    
    # Mask 2: Strategic & Simple
    mask_strategic = False
    if 'Biz_impact' in df.columns:
        mask_strategic = (df['Biz_impact'].astype(str).str.contains('전략과제', na=False)) & (df['Status'] == '단순 인입')
        
    # Combined Mask
    final_mask = mask_status | mask_strategic
    
    if not isinstance(final_mask, bool) and not final_mask.any(): # Handle empty or all False
         return pd.DataFrame()
         
    issues = df[final_mask].copy()
    
    # Define Issue Type and Sort Order
    # We want Status Issue at top.
    
    def get_issue_type_sort(row):
        # 1. Status Issue
        status_val = str(row['Status']) if pd.notna(row['Status']) else ''
        if status_val == '이슈':
            return 0, status_val # Use Status value
            
        # 2. Strategic Task
        biz_impact = str(row.get('Biz_impact', ''))
        # Strategic task definition: Status='단순 인입' AND Biz_impact contains '전략과제'
        # But wait, original logic was Status='단순 인입' AND Biz_impact contains '전략과제'
        # The user request says: "Strategic Task: Biz_impact와 똑같은 value로 표기"
        
        is_strategic = '전략과제' in biz_impact
        is_simple = status_val == '단순 인입'
        
        if is_strategic and is_simple:
            return 1, biz_impact # Use Biz_impact value
            
        return 2, 'Other'

    # Apply to create sort key and label
    applied = issues.apply(get_issue_type_sort, axis=1, result_type='expand')
    issues['Sort_Key'] = applied[0]
    issues['Issue_Type'] = applied[1]
    
    # Sort
    issues = issues.sort_values(by=['Sort_Key', 'End'], ascending=[True, True])
    
    return issues

def calculate_utilization_metrics(df_tasks: pd.DataFrame, df_resource: pd.DataFrame = None, df_weights: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculates utilization metrics per squad combining Task data and Resource data.
    """
    # 1. Base Workload from Tasks
    if df_tasks.empty:
        squad_summary = pd.DataFrame(columns=['Squad', 'Total_Tasks', 'Active_Tasks'])
    else:
        # Calculate Active Count: Start <= Today <= End
        today_date = pd.Timestamp(datetime.now().date())
        
        # Ensure Start and End are datetime
        start_col = pd.to_datetime(df_tasks['Start'], errors='coerce')
        end_col = pd.to_datetime(df_tasks['End'], errors='coerce')
        
        # Active if: Status is '진행 중' OR (Start_Date <= Today <= End_Date)
        is_in_progress = df_tasks['Status'] == '진행 중'
        is_in_range = (start_col <= today_date) & (end_col >= today_date)
        active_mask = is_in_progress | is_in_range

        squad_summary = df_tasks.groupby('Squad').agg(
            Total_Tasks=('Task', 'count')
        ).reset_index()

        active_counts = df_tasks[active_mask].groupby('Squad').size().reset_index(name='Active_Tasks_Calc')
        
        # Merge to ensure 0 for no active tasks
        squad_summary = pd.merge(squad_summary, active_counts, on='Squad', how='left')
        squad_summary['Active_Tasks'] = squad_summary['Active_Tasks_Calc'].fillna(0)
        squad_summary = squad_summary.drop(columns=['Active_Tasks_Calc'])
        
        # Calculate Active_Tasks_Score using weights
        active_tasks_df = df_tasks[active_mask].copy()
        
        weight_map = {}
        if df_weights is not None and not df_weights.empty:
            type_col = next((c for c in df_weights.columns if str(c).strip().lower() == 'type'), None)
            weight_col = next((c for c in df_weights.columns if str(c).strip().lower() == 'weight'), None)
            if type_col and weight_col:
                for _, row in df_weights.iterrows():
                    t = str(row[type_col]).strip()
                    w = pd.to_numeric(row[weight_col], errors='coerce')
                    if pd.notna(w) and t:
                        weight_map[t] = float(w)
                        
        def get_task_weight(type_val):
            if pd.isna(type_val) or str(type_val).strip() == "":
                return 1.0 # Default weight is 1.0
            type_str = str(type_val).strip()
            return weight_map.get(type_str, 1.0)
            
        if 'Type' in active_tasks_df.columns:
            active_tasks_df['Task_Weight'] = active_tasks_df['Type'].apply(get_task_weight)
        else:
            active_tasks_df['Task_Weight'] = 1.0
            
        active_scores = active_tasks_df.groupby('Squad')['Task_Weight'].sum().reset_index(name='Active_Tasks_Score')
        
        squad_summary = pd.merge(squad_summary, active_scores, on='Squad', how='left')
        squad_summary['Active_Tasks_Score'] = squad_summary['Active_Tasks_Score'].fillna(0)

    if df_resource is None or df_resource.empty:
        # Return basic stats if no resource data, but ensure columns exist for UI consistency
        squad_summary['Headcount'] = 0
        squad_summary['Min_Personnel'] = 0
        squad_summary['Capacity_Score'] = 0.0
        squad_summary['Total_Load_Score'] = squad_summary['Active_Tasks_Score'] if 'Active_Tasks_Score' in squad_summary.columns else 0.0
        squad_summary['Shortage'] = 0.0
        return squad_summary

    # 2. Merge with Resource Data
    # df_resource expected columns: Squad, Headcount, Min_Personnel
    merged = pd.merge(squad_summary, df_resource, on='Squad', how='left')
    
    # Fill missing resource info with defaults
    merged['Headcount'] = merged['Headcount'].fillna(0)
    merged['Min_Personnel'] = merged['Min_Personnel'].fillna(1.0) # Avoid div/0
    
    # 3. Calculate Metrics
    def calc_row(row):
        headcount = pd.to_numeric(row['Headcount'], errors='coerce')
        if pd.isna(headcount): headcount = 0
            
        min_p = pd.to_numeric(row['Min_Personnel'], errors='coerce')
        if pd.isna(min_p) or min_p <= 0: min_p = 1.0
        
        active_count = row['Active_Tasks']
        total_load_score = row.get('Active_Tasks_Score', active_count)
        
        # A. Capacity Score: (보유인원 / 최소인원) * 5.0 * 0.8
        capacity_score = (headcount / min_p) * 5.0 * 0.8
        
        # B. Total Load Score
        # Already calculated as total_load_score
        
        # C. Shortage: (Total Load Score - Capacity Score) / Unit Score
        # Unit Score = 4.0 / Min_Personnel
        unit_score = 4.0 / min_p
        shortage = round((total_load_score - capacity_score) / unit_score, 1) if unit_score > 0 else 0.0
        
        return pd.Series([capacity_score, total_load_score, shortage])

    merged[['Capacity_Score', 'Total_Load_Score', 'Shortage']] = merged.apply(calc_row, axis=1)
    
    # [User Request] Filter out '미정' and '공통' squads
    merged = merged[~merged['Squad'].isin(['미정', '공통'])]

    return merged

