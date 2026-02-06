import pandas as pd

try:
    df = pd.read_excel("squad_order_0206.xlsx")
    print("Columns:", list(df.columns))
    print("First 10 rows:")
    print(df.head(10))
except Exception as e:
    print(f"Error: {e}")
