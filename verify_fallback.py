import pandas as pd
from logic import apply_sorting, get_squad_order, SQUAD_ORDER_FILE
import os

def test_squad_fallback():
    # 1. Test normal case (with file)
    print("--- Test 1: With valid Excel file ---")
    order = get_squad_order()
    print(f"Order loaded: {order}")
    if len(order) > 0:
        print("SUCCESS: Loaded order from file.")
    else:
        print("FAILED: Did not load order from file.")

    # 2. Test fallback case (simulate missing file)
    print("\n--- Test 2: With missing file (Fallback) ---")
    # Temporarily rename the file
    if os.path.exists(SQUAD_ORDER_FILE):
        os.rename(SQUAD_ORDER_FILE, SQUAD_ORDER_FILE + ".bak")
    
    try:
        order_fallback = get_squad_order()
        print(f"Fallback order loaded: {order_fallback}")
        
        if order_fallback == []:
            print("SUCCESS: Fallback is empty list.")
        else:
            print(f"FAILED: Fallback is NOT empty list: {order_fallback}")
            
        # Verify strict alphabetical sorting if order is empty
        data = {
            'Squad': ['C', 'A', 'B'],
            'Task': [1, 2, 3],
            'Start': pd.to_datetime(['2023-01-01']*3),
            'End': pd.to_datetime(['2023-01-02']*3),
            'Status': ['Ready']*3
        }
        df = pd.DataFrame(data)
        sorted_df = apply_sorting(df)
        print("Sorted Squads (Fallback):", sorted_df['Squad'].tolist())
        
        if sorted_df['Squad'].tolist() == ['A', 'B', 'C']:
            print("SUCCESS: Fallback sorting is alphabetical.")
        else:
            print("FAILED: Fallback sorting is NOT alphabetcal.")
            
    finally:
        # Restore file
        if os.path.exists(SQUAD_ORDER_FILE + ".bak"):
            os.rename(SQUAD_ORDER_FILE + ".bak", SQUAD_ORDER_FILE)

if __name__ == "__main__":
    test_squad_fallback()
