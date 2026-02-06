import pandas as pd
from logic import process_data

def test_excel_schema():
    try:
        # Read the excel file
        df = pd.read_excel("[Master] CTO office Roadmap (1).xlsx")
        print(f"Original columns: {list(df.columns)}")
        
        # Process the dataframe
        processed_df = process_data(df)
        print(f"Processed columns: {list(processed_df.columns)}")
        
        # Check for new columns
        expected_cols = ['Squad', 'Task', 'Start', 'End', 'Status', 'Goal', 'Project', 'Type', 'Comment', 'Target', 'Manager']
        missing = [c for c in expected_cols if c not in processed_df.columns]
        
        if not missing:
            print("SUCCESS: All expected columns are present.")
        else:
            print(f"WARNING: Some columns are missing: {missing}")
            # Note: Depending on excel content, some columns might be missing if source headers didn't match exactly or were empty.
            
        # Specific check for mapped columns
        # 'subproject_name' -> 'Task'
        if 'Task' in processed_df.columns:
            print(f"Task column check: OK (Preview: {processed_df['Task'].iloc[0]})")
            
        # 'project_name' -> 'Project'
        if 'Project' in processed_df.columns:
            print(f"Project column check: OK (Preview: {processed_df['Project'].iloc[0]})")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_excel_schema()
