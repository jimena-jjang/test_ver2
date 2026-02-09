import sys
from unittest.mock import MagicMock

# Mock streamlit before importing gsheet_handler
mock_st = MagicMock()
mock_st.cache_data = lambda ttl=600: lambda func: func # Mock decorator
sys.modules["streamlit"] = mock_st

# Mock gspread if it's not installed (though it should be)
try:
    import gspread
except ImportError:
    mock_gspread = MagicMock()
    mock_gspread.WorksheetNotFound = Exception
    sys.modules["gspread"] = mock_gspread

# Now import the module to test
try:
    import gsheet_handler
except ImportError as e:
    print(f"FAILED to import gsheet_handler: {e}")
    sys.exit(1)

# Test Logic
def run_tests():
    print("Running tests...")
    
    mock_sheet = MagicMock()
    mock_ws1 = MagicMock()
    mock_ws1.title = "Sheet1"
    mock_ws1.id = 0
    
    mock_ws2 = MagicMock()
    mock_ws2.title = "TargetSheet"
    mock_ws2.id = 12345
    
    # Mock worksheets()
    mock_sheet.worksheets.return_value = [mock_ws1, mock_ws2]
    
    # Mock get_worksheet()
    def get_worksheet_side_effect(arg):
        if arg == 0: return mock_ws1
        if arg == 1: return mock_ws2
        return None
    mock_sheet.get_worksheet.side_effect = get_worksheet_side_effect
    
    # Mock worksheet()
    def worksheet_side_effect(name):
        if name == "Sheet1": return mock_ws1
        if name == "TargetSheet": return mock_ws2
        if hasattr(gsheet_handler, 'gspread'):
            raise gsheet_handler.gspread.WorksheetNotFound
        else:
            raise Exception("WorksheetNotFound") # Fallback if mocked
            
    mock_sheet.worksheet.side_effect = worksheet_side_effect
    
    # Test 1: By Name
    ws = gsheet_handler._get_worksheet(mock_sheet, "TargetSheet")
    if ws != mock_ws2:
        print("FAIL: Find by Name")
        return False
        
    # Test 2: By GID (String)
    ws = gsheet_handler._get_worksheet(mock_sheet, "12345")
    if ws != mock_ws2:
        print("FAIL: Find by GID (String)")
        return False
        
    # Test 3: By Index (Int)
    ws = gsheet_handler._get_worksheet(mock_sheet, 0)
    if ws != mock_ws1:
        print("FAIL: Find by Index")
        return False
        
    # Test 4: Not Found
    ws = gsheet_handler._get_worksheet(mock_sheet, "Unknown")
    if ws is not None:
        print("FAIL: Should be None for unknown")
        return False
        
    print("SUCCESS: All tests passed!")
    return True

if __name__ == "__main__":
    if run_tests():
        sys.exit(0)
    else:
        sys.exit(1)
