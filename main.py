import os
import glob
import fitz # PyMuPDF
import pandas as pd
from src.config import OUTPUT_DIR, DATA_DIR, HEADER_ORDER
from src.parser import parse_race_form
from src.metrics_parser import parse_timing_metrics
from src.trainer_parser import parse_trainer_blocks
from src.box_parser import parse_box_history
from src.comment_parser import parse_comments_and_conditions
from src.form_parser import parse_last_start
from src.classification_parser import parse_classification
from src.conditions_parser import parse_conditions_banner
from src.trainer_lookup_service import enrich_trainer_metadata
from src.box_bias_calculator import load_box_bias_lookup
from src.merger import merge_all
from src.features import compute_features
from src.exporter import save_outputs
from src.diagnostic import Diagnostics




def extract_text(pdf_path: str) -> str:
text = []
with fitz.open(pdf_path) as doc:
for page in doc:
text.append(page.get_text())
return "\n".join(text)




def main():
os.makedirs(OUTPUT_DIR, exist_ok=True)


pdf_paths = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
if not pdf_paths:
print("❌ No PDFs found in data/")
return


diag = Diagnostics()
all_frames = []


# Optional enrichment lookups
box_bias_map = load_box_bias_lookup(os.path.join(OUTPUT_DIR, "archived"))
trainer_cache = enrich_trainer_metadata()


for path in pdf_paths:
print(f"📄 Processing: {os.path.basename(path)}")
raw = extract_text(path)


main()
