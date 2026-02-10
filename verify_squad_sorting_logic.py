
import pandas as pd
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append('.')

import utils

class TestSquadSorting(unittest.TestCase):
    
    @patch('utils.load_squad_order_from_sheet')
    def test_sorting_with_sheet_order(self, mock_load_order):
        # Mock the sheet return
        mock_load_order.return_value = ['Squad A', 'Squad B']
        
        # Create sample data
        data = {
            'Squad': ['Squad C', 'Squad A', 'Squad B', 'Squad A'],
            'Task': ['T1', 'T2', 'T3', 'T4'],
            'Start': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-02'],
            'End': ['2023-01-05', '2023-01-05', '2023-01-05', '2023-01-06'],
            'Status': ['진행 중', '진행 중', '진행 중', '진행 중']
        }
        df = pd.DataFrame(data)
        
        # Save to temporary excel to pass to load_and_process_data
        temp_file = 'temp_test_squads.xlsx'
        df.to_excel(temp_file, index=False)
        
        # Run processing
        processed_df = utils.load_and_process_data(temp_file)
        
        # Check order
        # Expected: Squad A, Squad B (from order), then Squad C (undefined, at end)
        
        # Get unique squads in order of appearance in the processed dataframe
        # Note: load_and_process_data sorts by Squad, Goal, Group, Start
        # We need to preserve the categorical order or the sort order
        
        # The function converts Squad to Categorical with specific order
        print("Categories:", processed_df['Squad'].cat.categories.tolist())
        
        expected_order = ['Squad A', 'Squad B', 'Squad C']
        self.assertEqual(processed_df['Squad'].cat.categories.tolist(), expected_order)
        
        # Verify the actual data is sorted accordingly
        # The dataframe is sorted by Sort Cols which includes Squad
        unique_squads_in_df = processed_df['Squad'].unique().tolist()
        self.assertEqual(unique_squads_in_df, expected_order)
        
        print("Test passed: Squads sorted as A, B, C (undefined at end)")

if __name__ == '__main__':
    unittest.main()
