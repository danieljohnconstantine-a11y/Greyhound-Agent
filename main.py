# main.py
import os
import glob
import fitz  # PyMuPDF
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
    # Read text from all pages
    text = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)

def main() -> None:
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

        # Parse each section
        df_core = parse_race_form(raw)
        df_metrics = parse_timing_metrics(raw)
        df_trainer = parse_trainer_blocks(raw, trainer_cache)
        df_box = parse_box_history(raw, box_bias_map)
        df_comment, df_conditions = parse_comments_and_conditions(raw)
        df_last_start = parse_last_start(raw)
        df_class = parse_classification(raw)
        df_cond_banner = parse_conditions_banner(raw)

        # Merge all partial frames into one race-level DataFrame
        merged = merge_all(
            [
                df_core, df_metrics, df_trainer, df_box,
                df_comment, df_conditions, df_last_start,
                df_class, df_cond_banner
            ],
            header_order=HEADER_ORDER
        )

        # Assign the source PDF name for traceability
        merged["SourcePDF"] = os.path.basename(path)

        # Compute derived features
        merged = compute_features(merged)

        # Diagnostics per PDF
        diag.audit_one_pdf(merged, source=os.path.basename(path))

        all_frames.append(merged)

    # Concatenate all PDF outputs
    if all_frames:
        final_df = pd.concat(all_frames, ignore_index=True)
        diag.audit_final(final_df)  # write audit summary
        save_outputs(final_df)
    else:
        print("❌ No data extracted.")

if __name__ == "__main__":
    main()
