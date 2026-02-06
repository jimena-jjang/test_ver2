import pandas as pd
from logic import apply_sorting, get_squad_order

def test_squad_sorting():
    print("Loading Squad Order...")
    order = get_squad_order()
    print(f"Order loaded: {order}")
    
    # Create valid dummy data with Squads from the order file and some others
    data = {
        'Squad': ['Devops', '공통', 'UnknownSquad', '회원', '커머스'],
        'Task': ['A', 'B', 'C', 'D', 'E'],
        'Start': pd.to_datetime(['2023-01-01']*5),
        'End': pd.to_datetime(['2023-01-02']*5),
        'Status': ['Ready']*5
    }
    df = pd.DataFrame(data)
    
    print("\nBefore Sorting:")
    print(df['Squad'].tolist())
    
    sorted_df = apply_sorting(df)
    
    print("\nAfter Sorting:")
    print(sorted_df['Squad'].tolist())
    
    # Validation
    # According to file: 공통(1), 커머스(2), 회원(5), Devops(8)
    # UnknownSquad should be last (sorted alphabetically if multiple)
    
    expected_order = ['공통', '커머스', '회원', 'Devops', 'UnknownSquad']
    actual_order = sorted_df['Squad'].tolist()
    
    if actual_order == expected_order:
        print("SUCCESS: Sorting matches expected order.")
    else:
        print(f"FAILED: Expected {expected_order}, got {actual_order}")

if __name__ == "__main__":
    test_squad_sorting()
