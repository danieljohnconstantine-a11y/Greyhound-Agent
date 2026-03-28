import pandas as pd
import os
import numpy as np

def export_to_excel(df, output_path, filename=None):
    """
    Export DataFrame to Excel with all columns preserved.
    
    Args:
        df: pandas DataFrame with dog data
        output_path: directory to save Excel file
        filename: optional filename (default: greyhound_analysis_TIMESTAMP.xlsx)
    
    Returns:
        filepath: path to saved Excel file
    """
    df = df.copy()
    
    # Flatten list fields for Excel compatibility
    list_columns = df.select_dtypes(include=['object']).columns
    for col in list_columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, list) else x)
    
    # Define preferred column order (common fields first)
    priority_cols = [
        "Track", "RaceNumber", "RaceDate", "RaceTime", "Distance",
        "Box", "DogName", "FormNumber", "Trainer", "SexAge", "Weight", "Draw",
        "CareerWins", "CareerPlaces", "CareerStarts", "PrizeMoney",
        "RTC", "DLR", "DLW", "FinalScore"
    ]
    
    # Keep existing columns in priority order, then add remaining
    existing_priority = [col for col in priority_cols if col in df.columns]
    remaining = [col for col in df.columns if col not in priority_cols]
    ordered_cols = existing_priority + remaining
    df = df[ordered_cols]
    
    # Validation: Report statistics for key fields
    print("\n📊 Data Validation Report:")
    print(f"   Total dogs: {len(df)}")
    
    # Check timing data source
    if "TimingDataSource" in df.columns:
        timing_sources = df["TimingDataSource"].value_counts()
        print(f"\n   Timing Data Source:")
        for source, count in timing_sources.items():
            print(f"   - {source}: {count} dogs")
    
    # Check for unique values in key parsed fields
    key_fields = ["DogName", "Box", "Trainer", "CareerWins", "PrizeMoney", "Distance"]
    print(f"\n   Parsed Fields (from PDF):")
    for field in key_fields:
        if field in df.columns:
            unique_count = df[field].nunique()
            null_count = df[field].isnull().sum()
            print(f"   ✅ {field}: {unique_count} unique values, {null_count} missing")
    
    # Check computed fields
    computed_fields = ["BestTimeSec", "SectionalSec", "Last3TimesSec", "Margins", "FinalScore"]
    print(f"\n   Computed/Derived Fields:")
    for field in computed_fields:
        if field in df.columns:
            unique_count = df[field].nunique()
            null_count = df[field].isnull().sum()
            if unique_count == 1:
                print(f"   ⚠️  {field}: ALL {len(df)} dogs have identical value (not unique)")
            else:
                print(f"   ✅ {field}: {unique_count} unique values, {null_count} missing")
    
    # Anomaly detection
    print(f"\n   Anomaly Detection:")
    anomalies_found = False
    
    # Check for missing critical fields
    critical_fields = ["DogName", "Track", "RaceNumber", "Distance", "Box"]
    for field in critical_fields:
        if field in df.columns:
            missing = df[field].isnull().sum()
            if missing > 0:
                print(f"   ⚠️  {field}: {missing} dogs have missing values")
                anomalies_found = True
    
    # Check for duplicate dog names in same race
    duplicates = df.groupby(["Track", "RaceNumber", "DogName"]).size()
    duplicates = duplicates[duplicates > 1]
    if len(duplicates) > 0:
        print(f"   ⚠️  Found {len(duplicates)} duplicate dog entries in same race")
        anomalies_found = True
    
    # Check for unrealistic values
    if "Weight" in df.columns:
        zero_weight = (df["Weight"] == 0).sum()
        if zero_weight > 0:
            print(f"   ⚠️  {zero_weight} dogs have Weight = 0 (missing data)")
            anomalies_found = True
    
    if "PrizeMoney" in df.columns:
        zero_prize = (df["PrizeMoney"] == 0).sum()
        if zero_prize > 0:
            print(f"   ℹ️  {zero_prize} dogs have PrizeMoney = 0 (may be normal for new dogs)")
    
    if "CareerStarts" in df.columns:
        zero_starts = (df["CareerStarts"] == 0).sum()
        if zero_starts > 0:
            print(f"   ℹ️  {zero_starts} dogs have CareerStarts = 0 (new/unraced dogs)")
    
    if not anomalies_found:
        print(f"   ✅ No critical anomalies detected")
    
    # Save to Excel
    if filename is None:
        filename = f"greyhound_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(output_path, filename)
    
    # Ensure directory exists
    os.makedirs(output_path, exist_ok=True)
    
    try:
        # Use openpyxl engine for Excel export (requires: pip install openpyxl)
        df.to_excel(filepath, index=False, engine='openpyxl')
    except ImportError:
        raise ImportError(
            "openpyxl is required for Excel export. Install with: pip install openpyxl"
        )
    except Exception as e:
        raise Exception(f"Failed to export Excel file: {str(e)}")
    
    print(f"\n✅ EXCEL SAVED: {filepath}")
    print(f"   Columns exported: {len(df.columns)}")
    print(f"   Rows exported: {len(df)}")
    
    return filepath
