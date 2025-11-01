import os
import pandas as pd
from .config import LOG_DIR


class Diagnostics:
def __init__(self):
os.makedirs(LOG_DIR, exist_ok=True)
self.logs = []


def audit_one_pdf(self, df: pd.DataFrame, source: str):
missing = df.isna().sum().sort_values(ascending=False)
row = {
"source": source,
"rows": len(df),
"missing_top10": missing.head(10).to_dict(),
}
self.logs.append(row)


def audit_final(self, df: pd.DataFrame):
audit_path = os.path.join(LOG_DIR, "audit_summary.csv")
pd.DataFrame(self.logs).to_csv(audit_path, index=False)
print(f"🧪 Diagnostics saved → {audit_path}")
