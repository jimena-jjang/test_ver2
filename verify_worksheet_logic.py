import unittest
from unittest.mock import MagicMock
import pandas as pd
import gsheet_handler

class TestWorksheetLogic(unittest.TestCase):
    def setUp(self):
        self.mock_sheet = MagicMock()
        self.mock_ws1 = MagicMock()
        self.mock_ws1.title = "Sheet1"
        self.mock_ws1.id = 0
        
        self.mock_ws2 = MagicMock()
        self.mock_ws2.title = "TargetSheet"
        self.mock_ws2.id = 12345
        
        # Setup mock behavior
        self.mock_sheet.worksheets.return_value = [self.mock_ws1, self.mock_ws2]
        
        def get_worksheet_side_effect(arg):
            if isinstance(arg, int):
                # In gspread, get_worksheet(0) gets by index
                if arg == 0: return self.mock_ws1
                if arg == 1: return self.mock_ws2
                return None
            return None
            
        self.mock_sheet.get_worksheet.side_effect = get_worksheet_side_effect
        
        def worksheet_side_effect(name):
            if name == "Sheet1": return self.mock_ws1
            if name == "TargetSheet": return self.mock_ws2
            raise gsheet_handler.gspread.WorksheetNotFound
            
        self.mock_sheet.worksheet.side_effect = worksheet_side_effect

    def test_find_by_name(self):
        ws = gsheet_handler._get_worksheet(self.mock_sheet, "TargetSheet")
        self.assertEqual(ws, self.mock_ws2)
        
    def test_find_by_gid_int(self):
        # This relies on the loop logic in _get_worksheet
        ws = gsheet_handler._get_worksheet(self.mock_sheet, "12345")
        self.assertEqual(ws, self.mock_ws2)
        
    def test_find_by_index_int(self):
        ws = gsheet_handler._get_worksheet(self.mock_sheet, 0)
        self.assertEqual(ws, self.mock_ws1)

    def test_not_found(self):
        ws = gsheet_handler._get_worksheet(self.mock_sheet, "NonExistent")
        self.assertIsNone(ws)

if __name__ == '__main__':
    unittest.main()
