import os, glob, json, time, sys
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

def _extract_text(pdf_path: str) -> str:
    parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts)

def _validate_headers(df: pd.DataFrame) -> None:
    """Hard, in-process validation to keep automation simple."""
    os.makedirs(os.path.join(OUTPUT_DIR, "logs"), exist_ok=True)
    expected = list(HEADER_ORDER)
    produced = list(df.columns)

    missing = [c for c in expected if c not in produced]
    extra   = [c for c in produced if c not in expected]
    misaligned = []
    if not missing and not extra:
        for i, (e, g) in enumerate(zip(expected, produced)):
            if e != g:
                misaligned.append((i, e, g))
    empty_cols = [c for c in expected if c in df.columns and df[c].isna().all()]

    preview_path = os.path.join(OUTPUT_DIR, "logs", "preview_head_10.csv")
    df.head(10).to_csv(preview_path, index=False)

    report = {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "expected_cols": len(expected),
        "missing": missing,
        "extra": extra,
        "misaligned": misaligned,
        "empty_columns": empty_cols[:50],
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(os.path.join(OUTPUT_DIR, "logs", "header_audit.json"), "w") as f:
        json.dump(report, f, indent=2)
    pd.DataFrame([report]).to_csv(os.path.join(OUTPUT_DIR, "logs", "header_audit.csv"), index=False)

    # Fail fast in CI if schema is off
    if missing or extra or misaligned:
        print("❌ Header schema mismatch. See outputs/logs/header_audit.*")
        sys.exit(2)
    print("✅ Headers OK. Preview saved:", preview_path)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    if not pdfs:
        print("❌ No PDFs in data/")
        sys.exit(1)

    diag = Diagnostics()
    frames = []

    box_bias_map = load_box_bias_lookup(os.path.join(OUTPUT_DIR, "archived"))
    trainer_cache = enrich_trainer_metadata()

    for p in pdfs:
        print("📄 Processing", os.path.basename(p))
        text = _extract_text(p)

        df_core = parse_race_form(text)
        df_metrics = parse_timing_metrics(text)
        df_trainer = parse_trainer_blocks(text, trainer_cache)
        df_box = parse_box_history(text, box_bias_map)
        df_comment, df_conditions = parse_comments_and_conditions(text)
        df_last = parse_last_start(text)
        df_class = parse_classification(text)
        df_banner = parse_conditions_banner(text)

        merged = merge_all(
            [df_core, df_metrics, df_trainer, df_box,
             df_comment, df_conditions, df_last, df_class, df_banner],
            header_order=HEADER_ORDER
        )
        merged["SourcePDF"] = os.path.basename(p)
        merged = compute_features(merged)
        frames.append(merged)
        diag.audit_one_pdf(merged, source=os.path.basename(p))

    if not frames:
        print("❌ No parsed data.")
        sys.exit(1)

    final_df = pd.concat(frames, ignore_index=True).drop_duplicates()
    diag.audit_final(final_df)
    save_outputs(final_df)  # writes .xlsx + .csv to outputs/

    # ✅ embedded validation here
    _validate_headers(final_df)

if __name__ == "__main__":
    main()
