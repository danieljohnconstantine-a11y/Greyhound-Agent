import os
import pandas as pd
from datetime import datetime


from .config import OUTPUT_DIR


def save_outputs(df: pd.DataFrame):
ts = datetime.now().strftime("%Y%m%d_%H%M%S")


csv_path = os.path.join(OUTPUT_DIR, f"todays_form_{ts}.csv")
xlsx_path = os.path.join(OUTPUT_DIR, f"todays_form_{ts}.xlsx")


df.to_csv(csv_path, index=False)
try:
df.to_excel(xlsx_path, index=False)
print(f"✅ Excel saved → {xlsx_path}")
except Exception as e:
print(f"⚠️ Excel save failed ({e}); CSV saved → {csv_path}")
print(f"✅ CSV saved → {csv_path}")
