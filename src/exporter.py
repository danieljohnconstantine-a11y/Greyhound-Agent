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
    print("\n   Computed/Derived Fields:")
    for field in computed_fields:
        if field in df.columns:
            unique_count = df[field].nunique()
            null_count = df[field].isnull().sum()
            if unique_count == 1:
                print(f"   ⚠️  {field}: ALL {len(df)} dogs have identical value (not unique)")
            else:
                print(f"   ✅ {field}: {unique_count} unique values, {null_count} missing")
    
    # Save to Excel
    if filename is None:
        filename = f"greyhound_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(output_path, filename)
    
    # Ensure directory exists
    os.makedirs(output_path, exist_ok=True)
    
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"\n✅ EXCEL SAVED: {filepath}")
    print(f"   Columns exported: {len(df.columns)}")
    print(f"   Rows exported: {len(df)}")
    
    return filepath
