import pandas as pd
from squad_manager import sort_squads, get_squad_order
from logic import apply_sorting

def test_refactor():
    print("Checking squad_manager...")
    order = get_squad_order()
    print(f"Order: {order}")
    
    squads = ['Unknown', '회원', '공통', 'APP']
    sorted_squads = sort_squads(squads)
    print(f"Sorted list: {sorted_squads}")
    
    # Expected: 공통 -> 회원 -> APP -> Unknown (because 공통 is 1, 회원 5, APP 6 in excel)
    # Note: If excel is loaded, 공통(1) matches. 회원(5), APP(6). 
    
    print("\nChecking logic.py integration...")
    data = {
        'Squad': squads,
        'Task': [1, 2, 3, 4],
        'Start': pd.to_datetime(['2023-01-01']*4),
        'End': pd.to_datetime(['2023-01-02']*4),
        'Status': ['Ready']*4
    }
    df = pd.DataFrame(data)
    df_sorted = apply_sorting(df)
    print(f"Logic Sorted Squads: {df_sorted['Squad'].tolist()}")
    
    if df_sorted['Squad'].tolist() == sorted_squads:
        print("SUCCESS: logic.py applies same sorting as squad_manager.")
    else:
        print("FAILED: logic.py sorting mismatch.")

if __name__ == "__main__":
    test_refactor()
