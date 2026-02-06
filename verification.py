import pandas as pd
from datetime import datetime, timedelta
from logic import calculate_utilization_metrics

def test_utilization():
    # 1. Mock Task Data
    today = datetime.now()
    tasks_data = {
        'Squad': ['A', 'A', 'B', 'C'],
        'Task': ['T1', 'T2', 'T3', 'T4'],
        'Start': [today - timedelta(days=5), today + timedelta(days=1), today - timedelta(days=2), today - timedelta(days=10)],
        'End':   [today + timedelta(days=5), today + timedelta(days=10), today + timedelta(days=2), today - timedelta(days=1)],
        'Status': ['진행 중', '진행 예정', '진행 중', '진행 완료']
    }
    # T1: Active (Start <= Today <= End)
    # T2: Inactive (Start > Today)
    # T3: Active
    # T4: Inactive (End < Today)
    
    df_tasks = pd.DataFrame(tasks_data)
    
    # 2. Mock Resource Data
    resource_data = {
        'Squad': ['A', 'B', 'C'],
        'Headcount': [10, 5, 2],
        'Min_Personnel': [2, 1, 1]
    }
    df_resource = pd.DataFrame(resource_data)
    
    # 3. Run Calculation
    result = calculate_utilization_metrics(df_tasks, df_resource)
    
    print("Optimization Result:")
    print(result[['Squad', 'Total_Tasks', 'Active_Tasks', 'Capacity', 'Load_Rate', 'Balance']])
    
    # 4. Assertions
    # Squad A: 1 Active Task (T1). Capacity = 10/2 = 5. Load Rate = 1/5 = 0.2. Balance = 10 - (1*2) = 8.
    row_a = result[result['Squad'] == 'A'].iloc[0]
    assert row_a['Active_Tasks'] == 1, f"Expected 1 active task for A, got {row_a['Active_Tasks']}"
    assert row_a['Capacity'] == 5.0
    assert row_a['Load_Rate'] == 0.2
    assert row_a['Balance'] == 8.0
    
    # Squad B: 1 Active Task (T3). Capacity = 5/1 = 5. Load Rate = 1/5 = 0.2. Balance = 5 - 1 = 4.
    row_b = result[result['Squad'] == 'B'].iloc[0]
    assert row_b['Active_Tasks'] == 1
    
    # Squad C: 0 Active Tasks (T4 ended). Capacity = 2/1 = 2. Load Rate = 0. Balance = 2.
    row_c = result[result['Squad'] == 'C'].iloc[0]
    assert row_c['Active_Tasks'] == 0
    
    print("\n✅ All assertions passed!")

def test_process_resource():
    from utils import process_resource_dataframe
    import pandas as pd
    
    # Mock Raw DF
    data = {
        'Squad (대분류)': ['A', 'B'],
        '보유 인원': [10, 5],
        '과제당 최소 투입 인원': [2, 1]
    }
    raw = pd.DataFrame(data)
    
    processed = process_resource_dataframe(raw)
    
    assert processed is not None, "Processed DF is None"
    assert 'Squad' in processed.columns
    assert 'Headcount' in processed.columns
    assert 'Min_Personnel' in processed.columns
    assert processed.iloc[0]['Headcount'] == 10
    
    print("✅ process_resource_dataframe passed!")

if __name__ == "__main__":
    try:
        test_utilization()
        test_process_resource()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        exit(1)
