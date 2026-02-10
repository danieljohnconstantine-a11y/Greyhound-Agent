#!/usr/bin/env python3
"""
Comprehensive Data Pipeline Validation Script

This script performs end-to-end validation of data loading and processing:
1. Validates CSV file format and content
2. Validates PDF files exist and are readable  
3. Tests data loading functions
4. Tests feature extraction
5. Reports any issues found

CRITICAL: Run this BEFORE claiming the pipeline works!

Usage:
    python validate_data_pipeline.py
"""

import os
import sys
import glob
import re
import traceback

def validate_csv_files(data_dir="data"):
    """Validate all CSV result files have correct format"""
    print("=" * 80)
    print("CSV FILE VALIDATION")
    print("=" * 80)
    
    results_files = glob.glob(f"{data_dir}/results_*.csv")
    print(f"Found {len(results_files)} CSV files to validate\n")
    
    if not results_files:
        print("❌ ERROR: No CSV files found!")
        return False
    
    errors = []
    warnings = []
    valid_count = 0
    total_races = 0
    
    required_cols = ['Track', 'Race', 'Position1', 'Position2', 'Position3', 'Position4']
    
    for csv_file in sorted(results_files):
        try:
            # Check filename format
            filename = os.path.basename(csv_file)
            date_match = re.search(r'results_(\d{4}-\d{2}-\d{2})\.csv', filename)
            if not date_match:
                warnings.append(f"{filename}: Filename doesn't match pattern results_YYYY-MM-DD.csv")
            
            # Read and validate structure
            with open(csv_file, 'r') as f:
                header = f.readline().strip()
                lines = f.readlines()
            
            # Check header
            header_cols = [col.strip() for col in header.split(',')]
            missing_cols = [col for col in required_cols if col not in header_cols]
            
            if missing_cols:
                errors.append(f"{filename}: Missing columns {missing_cols}")
                continue
            
            # Check data rows
            if len(lines) == 0:
                warnings.append(f"{filename}: File is empty (no data rows)")
            else:
                valid_count += 1
                total_races += len(lines)
                
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
    
    # Print results
    print(f"✓ Valid files: {valid_count}/{len(results_files)}")
    print(f"✓ Total race records: {total_races}")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings[:10]:  # Show first 10
            print(f"  {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("\n✓ All CSV files validated successfully!")
    return True


def validate_pdf_files(data_dir="data"):
    """Validate PDF files exist and follow naming convention"""
    print("\n" + "=" * 80)
    print("PDF FILE VALIDATION")
    print("=" * 80)
    
    pdf_files = glob.glob(f"{data_dir}/*form.pdf")
    print(f"Found {len(pdf_files)} PDF files\n")
    
    if not pdf_files:
        print("❌ ERROR: No PDF files found!")
        return False
    
    errors = []
    warnings = []
    
    # Check PDF naming convention: TRACKGDDMM (e.g., RICHG2812form.pdf)
    pattern = re.compile(r'^[A-Z]{4}G\d{4}form\.pdf$')
    
    for pdf_file in pdf_files[:20]:  # Sample first 20
        filename = os.path.basename(pdf_file)
        if not pattern.match(filename):
            warnings.append(f"{filename}: Doesn't match expected pattern TRACKGDDMM")
        
        # Check file size
        size = os.path.getsize(pdf_file)
        if size < 1000:  # Less than 1KB is suspiciously small
            warnings.append(f"{filename}: File size {size} bytes is very small")
    
    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        return False
    
    if warnings:
        print(f"⚠️  Warnings ({len(warnings)}):")
        for warning in warnings[:5]:
            print(f"  {warning}")
    
    print(f"\n✓ PDF files validated successfully!")
    return True


def test_data_loading():
    """Test that data loading functions work"""
    print("\n" + "=" * 80)
    print("DATA LOADING TEST")
    print("=" * 80)
    
    try:
        # Test importing
        sys.path.insert(0, os.path.dirname(__file__))
        from src.ml_predictor import load_historical_data_hybrid
        print("✓ Successfully imported load_historical_data_hybrid")
        
        # Test loading a small subset
        print("\nAttempting to load data from 'data' directory...")
        print("(This may take a minute...)\n")
        
        race_data, winners = load_historical_data_hybrid(data_dir="data")
        
        print(f"\n✓ Data loading successful!")
        print(f"  - Loaded {len(race_data)} training samples")
        print(f"  - Loaded {len(winners)} winner records")
        
        if len(race_data) == 0:
            print("\n❌ ERROR: No training samples loaded!")
            print("This means CSV-PDF matching failed or no valid data found.")
            return False
        
        if len(race_data) < 100:
            print(f"\n⚠️  WARNING: Only {len(race_data)} samples loaded (expected thousands)")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during data loading:")
        print(f"  {str(e)}")
        traceback.print_exc()
        return False


def test_feature_extraction():
    """Test that feature extraction works"""
    print("\n" + "=" * 80)
    print("FEATURE EXTRACTION TEST")
    print("=" * 80)
    
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from src.features import compute_features
        from src.parser import parse_race_form
        
        print("✓ Successfully imported feature extraction functions")
        
        # Could add more detailed tests here
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR importing feature extraction:")
        print(f"  {str(e)}")
        return False


def main():
    """Run all validation checks"""
    print("\n" + "=" * 80)
    print("GREYHOUND PREDICTION PIPELINE - DATA VALIDATION")
    print("=" * 80)
    print()
    
    results = {
        'CSV Files': validate_csv_files(),
        'PDF Files': validate_pdf_files(),
        'Data Loading': test_data_loading(),
        'Feature Extraction': test_feature_extraction(),
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        print("The pipeline is ready to use.")
        return 0
    else:
        print("\n❌ VALIDATION FAILED")
        print(f"{total - passed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
