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
    '보류/이슈': {'color': '#EF4444'},
    '단순 인입': {'color': '#64748B'},
    'DROP': {'color': '#1F2937'},
}

STATUS_ORDER = [
    '진행 중',
    '진행 예정',
    '보류/이슈',
    '단순 인입',
    '진행 완료',
    'DROP'
]

DEFAULT_STATUS_COLOR = '#888888'

# -----------------------------------------------------------------------------
# DATA PROCESSING
# -----------------------------------------------------------------------------
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
        'main_goal': 'Main_Goal',
        'sub_goal': 'Sub_Goal',
        
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
    if 'Sub_Goal' in df.columns and 'Goal' not in df.columns:
        df['Goal'] = df['Sub_Goal']
    
    # Normalize strings
    string_cols = ['Squad', 'Task', 'Status', 'Goal', 'Main_Goal', 'Sub_Goal', 'Project', 'Type', 'Comment', 'Target', 'Manager', 'PM', 'PD', 'FE', 'BE', 'QA', 'Remarks']
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
    Returns tasks that are defined as issues.
    """
    # Assuming '보류/이슈' status or maybe overdue tasks
    issues = df[df['Status'] == '보류/이슈'].copy()
    
    # You could also add logic for overdue tasks: End < Today and Status != Done
    today = pd.Timestamp.now()
    overdue_mask = (df['End'] < today) & (~df['Status'].isin(['진행 완료', 'DROP', '보류/이슈']))
    overdue = df[overdue_mask].copy()
    overdue['Issue_Type'] = 'Overdue'
    
    issues['Issue_Type'] = 'Status Issue'
    
    return pd.concat([issues, overdue])
