import pytest
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path to import logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logic import process_data, apply_sorting, predict_start_date, identify_issues

@pytest.fixture
def sample_df():
    data = {
        'Squad': ['회원', '커머스', 'Unknown', '전사공통'],
        'Task': ['Task1', 'Task2', 'Task3', 'Task4'],
        'Status': ['진행 중', '진행 완료', '보류/이슈', '진행 예정'],
        'Start': ['2023-01-01', '2023-01-05', '2023-01-10', '2023-02-01'],
        'End': ['2023-01-10', '2023-01-15', '2023-01-20', '2023-02-10'],
        'Order': [2, 1, 3, 0]
    }
    df = pd.DataFrame(data)
    return process_data(df)

def test_process_data(sample_df):
    assert 'Squad' in sample_df.columns
    assert 'Start' in sample_df.columns
    assert pd.api.types.is_datetime64_any_dtype(sample_df['Start'])

from unittest.mock import patch

@patch('logic.get_squad_order')
def test_apply_sorting(mock_get_order, sample_df):
    # Mock the order to ensure '전사공통' is first
    mock_get_order.return_value = ['전사공통', '회원', '커머스']
    
    sorted_df = apply_sorting(sample_df)
    
    # Check if '전사공통' is first (Task4)
    assert sorted_df.iloc[0]['Task'] == 'Task4'
    
    # Check if 'Unknown' is last (Task3)
    assert sorted_df.iloc[-1]['Task'] == 'Task3'

def test_predict_start_date(sample_df):
    # For '커머스', max end is 2023-01-15
    predicted = predict_start_date(sample_df, '커머스')
    assert predicted == pd.Timestamp('2023-01-16')

def test_identify_issues(sample_df):
    issues = identify_issues(sample_df)
    # Task3 is '보류/이슈'
    assert 'Task3' in issues['Task'].values
    
    # Task1 is 'Start' 2023-01-01, End 2023-01-10. If today is later, it might be overdue?
    # Logic implementation check:
    # Overdue: End < Today AND Status not in [Done, DROP, Issue]
    # Task1 is '진행 중' and End is 2023-01-10. If we run this test now (2025), it should be overdue.
    
    # Mocking today is hard without injection, but 'Task1' should definitely be overdue in 2025/2026.
    assert 'Task1' in issues[issues['Issue_Type'] == 'Overdue']['Task'].values
