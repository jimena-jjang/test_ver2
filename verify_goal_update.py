import pandas as pd
from logic import process_data

def test_goal_update():
    try:
        # Read the NEW excel file
        # Note: Previous file was (1).xlsx, now (2).xlsx
        filename = "dummy_roadmap.xlsx"
        df = pd.read_excel(filename)
        print(f"Read {filename} successfully.")
        
        # Process the dataframe
        processed_df = process_data(df)
        print(f"Processed columns: {list(processed_df.columns)}")
        
        # Check for new Goal columns
        if 'Biz_impact' in processed_df.columns:
            print(f"Biz_impact check: OK (Ex: {processed_df['Biz_impact'].dropna().iloc[0]})")
        else:
            print("Biz_impact check: FAILED - Column missing")
            
        if 'Product_track' in processed_df.columns:
            print(f"Product_track check: OK (Ex: {processed_df['Product_track'].dropna().iloc[0]})")
        else:
            print("Product_track check: FAILED - Column missing")
            
        if 'Goal' in processed_df.columns:
            print(f"Goal check (derived): OK (Ex: {processed_df['Goal'].dropna().iloc[0]})")
        else:
            print("Goal check: FAILED - Column missing")

    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_goal_update()
