#!/usr/bin/env python3
"""
Fix CSV Column Names to Standard Format

This script standardizes all CSV files in data/ to use consistent column names:
- Renames 'Race' to 'RaceNumber' 
- Ensures all CSVs have Track, RaceNumber columns
"""

import pandas as pd
import glob
import os

def fix_csv_columns():
    """Fix column names in all CSV files to match expected format"""
    
    results_files = sorted(glob.glob("data/results_*.csv"))
    print(f"📁 Found {len(results_files)} results CSV files")
    print("=" * 80)
    
    fixed_count = 0
    skipped_count = 0
    
    for csv_file in results_files:
        try:
            df = pd.read_csv(csv_file)
            original_cols = list(df.columns)
            modified = False
            
            # Fix 'Race' or 'RaceNum' -> 'RaceNumber'
            if 'RaceNumber' not in df.columns:
                if 'Race' in df.columns:
                    df.rename(columns={'Race': 'RaceNumber'}, inplace=True)
                    modified = True
                    print(f"✅ Fixed {os.path.basename(csv_file)}: 'Race' → 'RaceNumber'")
                elif 'RaceNum' in df.columns:
                    df.rename(columns={'RaceNum': 'RaceNumber'}, inplace=True)
                    modified = True
                    print(f"✅ Fixed {os.path.basename(csv_file)}: 'RaceNum' → 'RaceNumber'")
            
            # Check if file now has required columns
            if 'Track' in df.columns and 'RaceNumber' in df.columns:
                if modified:
                    # Save fixed file
                    df.to_csv(csv_file, index=False)
                    fixed_count += 1
                else:
                    skipped_count += 1
            else:
                print(f"⚠️  Cannot fix {os.path.basename(csv_file)}: Missing required columns")
                print(f"   Columns: {original_cols}")
                skipped_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(csv_file)}: {e}")
            skipped_count += 1
    
    print("=" * 80)
    print(f"✅ Fixed {fixed_count} CSV files")
    print(f"⚠️  Skipped {skipped_count} CSV files")
    print()
    print("Files are now ready for training!")

if __name__ == "__main__":
    fix_csv_columns()
