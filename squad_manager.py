## 스쿼드 순서 관련 로직은 이 파일에서 중앙 관리

import pandas as pd
import unicodedata
import os

SQUAD_ORDER_FILE = "squad_order_0206.xlsx"

def get_squad_order():
    """
    Loads the squad order from the defined Excel file.
    Returns a list of squad names in order.
    Returns an empty list if file is not found or error occurs.
    """
    try:
        if not os.path.exists(SQUAD_ORDER_FILE):
             return []
             
        # Try to load from Excel
        order_df = pd.read_excel(SQUAD_ORDER_FILE)
        if 'squad' in order_df.columns:
            # Normalize and return list
            return order_df.sort_values('order')['squad'].astype(str).apply(lambda x: unicodedata.normalize('NFC', x)).tolist()
    except Exception as e:
        print(f"Failed to load squad order from {SQUAD_ORDER_FILE}: {e}")
    
    # Fallback to empty list
    return []

def sort_squads(squad_list):
    """
    Sorts a list of squads based on the defined order.
    Squads not in the order list are appended alphabetically.
    """
    order = get_squad_order()
    
    # If no order defined, just return sorted input
    if not order:
        return sorted(list(set(squad_list)))
        
    # Sort
    squad_set = set(squad_list)
    ordered_part = [s for s in order if s in squad_set]
    remainder = sorted([s for s in squad_list if s not in ordered_part])
    
    return ordered_part + remainder
