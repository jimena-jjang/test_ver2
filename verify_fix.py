import pandas as pd
from logic import calculate_utilization_metrics
from datetime import datetime

def test_missing_resource():
    # Mock Task Data only
    tasks_data = {
        'Squad': ['A', 'B'],
        'Task': ['T1', 'T2'],
        'Start': [datetime.now(), datetime.now()],
        'End':   [datetime.now(), datetime.now()],
        'Status': ['진행 중', '진행 중']
    }
    df_tasks = pd.DataFrame(tasks_data)
    
    # Call without resource df (None)
    result = calculate_utilization_metrics(df_tasks, None)
    
    print("Columns:", result.columns.tolist())
    
    # Assert columns exist
    required = ['Load_Rate', 'Capacity', 'Balance', 'Headcount', 'Min_Personnel']
    for col in required:
        assert col in result.columns, f"Missing {col}"
        
    print("✅ test_missing_resource Passed")

if __name__ == "__main__":
    test_missing_resource()
