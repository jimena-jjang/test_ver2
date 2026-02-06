import pandas as pd
from logic import process_data

def test_goal_update():
    try:
        # Read the NEW excel file
        # Note: Previous file was (1).xlsx, now (2).xlsx
        filename = "[Master] CTO office Roadmap (2).xlsx"
        df = pd.read_excel(filename)
        print(f"Read {filename} successfully.")
        
        # Process the dataframe
        processed_df = process_data(df)
        print(f"Processed columns: {list(processed_df.columns)}")
        
        # Check for new Goal columns
        if 'Main_Goal' in processed_df.columns:
            print(f"Main_Goal check: OK (Ex: {processed_df['Main_Goal'].dropna().iloc[0]})")
        else:
            print("Main_Goal check: FAILED - Column missing")

        if 'Sub_Goal' in processed_df.columns:
            print(f"Sub_Goal check: OK (Ex: {processed_df['Sub_Goal'].dropna().iloc[0]})")
        else:
            print("Sub_Goal check: FAILED - Column missing")
            
        if 'Goal' in processed_df.columns:
            print(f"Goal check (derived): OK (Ex: {processed_df['Goal'].dropna().iloc[0]})")
        else:
            print("Goal check: FAILED - Column missing")

    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_goal_update()
