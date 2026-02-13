
import pandas as pd
from logic import identify_issues

def verify():
    # Mock Data
    data = {
        'Squad': ['S1', 'S2', 'S3', 'S4'],
        'Task': ['Task A', 'Task B', 'Task C', 'Task D'],
        'Start': [pd.Timestamp('2023-01-01')] * 4,
        'End': [pd.Timestamp('2023-01-31')] * 4,
        'Status': ['이슈', '진행 중', '단순 인입', '단순 인입'],
        'Biz_impact': ['Normal', 'Normal', '전략과제 - Important', 'Normal'],
        'Comment': [''] * 4
    }
    df = pd.DataFrame(data)
    
    print("--- Input Data ---")
    print(df[['Task', 'Status', 'Biz_impact']])
    
    issues = identify_issues(df)
    
    print("\n--- Identified Issues ---")
    if not issues.empty:
        print(issues[['Task', 'Status', 'Biz_impact', 'Issue_Type']])
    else:
        print("No issues found.")
        
    # Validation
    # Task A: Status='이슈' -> Issue_Type should be '이슈'
    # Task C: Status='단순 인입', Biz_impact='전략과제 - Important' -> Issue_Type should be '전략과제 - Important'
    
    task_a = issues[issues['Task'] == 'Task A'].iloc[0]
    task_c = issues[issues['Task'] == 'Task C'].iloc[0]
    
    print("\n--- Validation Results ---")
    print(f"Task A (Status Issue): Expected '이슈', Got '{task_a['Issue_Type']}' -> {'PASS' if task_a['Issue_Type'] == '이슈' else 'FAIL'}")
    print(f"Task C (Strategic): Expected '전략과제 - Important', Got '{task_c['Issue_Type']}' -> {'PASS' if task_c['Issue_Type'] == '전략과제 - Important' else 'FAIL'}")

if __name__ == "__main__":
    verify()
