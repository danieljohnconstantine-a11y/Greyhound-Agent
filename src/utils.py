# src/utils.py (replace safe_concat_frames implementation)
def safe_concat_frames(frames, on_keys, how="left"):
    """
    Merge a list of DataFrames on the given keys, dropping any duplicate columns created by suffixes.
    Returns an empty DataFrame if all inputs are empty.
    """
    import pandas as pd

    base = None
    for f in frames:
        if f is None or f.empty:
            continue
        if base is None:
            base = f.copy()
        else:
            base = pd.merge(base, f, on=on_keys, how=how, suffixes=("", "_dup"))
            # Drop columns with '_dup' suffix from merge
            dup_cols = [c for c in base.columns if c.endswith("_dup")]
            base.drop(columns=dup_cols, inplace=True)
    return base if base is not None else pd.DataFrame()
