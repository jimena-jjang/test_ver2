import pandas as pd

try:
    df = pd.read_excel("[Master] CTO office Roadmap (2).xlsx", nrows=2)
    print("Columns:")
    for c in df.columns:
        print(c)
except Exception as e:
    print(f"Error reading excel: {e}")
