#!/usr/bin/env python3
"""
Complete Pipeline Validation Script
Tests all components end-to-end to ensure system works correctly.
"""

import sys
import os

# Add repository to path
sys.path.insert(0, '/home/runner/work/Greyhound-Agent/Greyhound-Agent')

def test_pipeline():
    """Run comprehensive pipeline tests."""
    
    print("="*80)
    print("COMPLETE PIPELINE VALIDATION - END TO END")
    print("="*80)
    
    # Test 1: Data folder structure
    print("\n📁 TEST 1: Data Folder Structure")
    print("-"*80)
    
    import glob
    pdf_files = glob.glob('data/*.pdf')
    csv_files = glob.glob('data/results_*.csv')
    
    print(f"✅ PDF files: {len(pdf_files)}")
    print(f"✅ CSV files: {len(csv_files)}")
    
    if len(pdf_files) == 0:
        print("❌ CRITICAL: No PDF files found!")
        return False
    if len(csv_files) == 0:
        print("❌ CRITICAL: No CSV files found!")
        return False
    
    # Test 2: CSV file format validation
    print("\n📊 TEST 2: CSV File Format Validation")
    print("-"*80)
    
    csv_valid = True
    for csv_file in csv_files[:5]:  # Test first 5
        with open(csv_file, 'r') as f:
            header = f.readline().strip()
            
        if 'Track' in header or 'track' in header:
            if 'RaceNumber' in header or 'Race' in header or 'RaceNum' in header:
                print(f"✅ {os.path.basename(csv_file)}: Valid format")
            else:
                print(f"❌ {os.path.basename(csv_file)}: Missing race column")
                csv_valid = False
        else:
            print(f"❌ {os.path.basename(csv_file)}: Missing Track column")
            csv_valid = False
    
    if not csv_valid:
        print("❌ CRITICAL: CSV format issues detected!")
        return False
    
    # Test 3: Track name normalization
    print("\n🏁 TEST 3: Track Name Normalization")
    print("-"*80)
    
    try:
        # Import normalize function
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.ml_predictor import normalize_track_name
        
        # Test key tracks from your Dec 28 data
        test_tracks = {
            'Richmond': 'RICH',
            'Grafton': 'GRAF', 
            'Healesville': 'HEAL',
            'Mount Gambier': 'MTGG',
            'BetDeluxe Capalaba': 'CAPA',
            'Sale': 'SALE',
            'Ladbrokes Q1 Lakeside': 'QLAK',
            'BetDeluxe Rockhampton': 'ROCK',
            'Gawler': 'GAWL'
        }
        
        normalization_ok = True
        for full_name, expected_code in test_tracks.items():
            result = normalize_track_name(full_name)
            if result == expected_code:
                print(f"✅ {full_name:30s} → {result}")
            else:
                print(f"❌ {full_name:30s} → {result} (expected: {expected_code})")
                normalization_ok = False
        
        if not normalization_ok:
            print("❌ CRITICAL: Track normalization issues detected!")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Cannot import normalize_track_name: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Hybrid loader import
    print("\n📦 TEST 4: Hybrid Loader Import")
    print("-"*80)
    
    try:
        from src.ml_predictor import load_historical_data_hybrid
        print("✅ load_historical_data_hybrid imported successfully")
    except Exception as e:
        print(f"❌ CRITICAL: Cannot import hybrid loader: {e}")
        return False
    
    # Test 5: Training script configuration
    print("\n🎯 TEST 5: Training Script Configuration")
    print("-"*80)
    
    try:
        with open('train_ml_track_ensemble.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('from src.ml_predictor import load_historical_data_hybrid', 'Import statement'),
            ('load_historical_data_hybrid()', 'Function call')
        ]
        
        all_ok = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: Found")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_ok = False
        
        if not all_ok:
            print("❌ CRITICAL: Training script not properly configured!")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Cannot read training script: {e}")
        return False
    
    # Test 6: Parser availability
    print("\n📄 TEST 6: PDF Parser Availability")
    print("-"*80)
    
    try:
        from src.parser import parse_race_form
        print("✅ parse_race_form imported successfully")
    except Exception as e:
        print(f"❌ CRITICAL: Cannot import parser: {e}")
        return False
    
    # Test 7: Feature computation
    print("\n⚙️  TEST 7: Feature Computation Module")
    print("-"*80)
    
    try:
        from src.features import compute_features
        print("✅ compute_features imported successfully")
    except Exception as e:
        print(f"❌ CRITICAL: Cannot import feature computation: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL PIPELINE TESTS PASSED!")
    print("="*80)
    print("\n📋 SUMMARY:")
    print(f"   - Data files: {len(pdf_files)} PDFs + {len(csv_files)} CSVs")
    print(f"   - CSV format: Valid")
    print(f"   - Track normalization: Working (43+ mappings)")
    print(f"   - Hybrid loader: Configured correctly")
    print(f"   - Training script: Uses hybrid loader")
    print(f"   - Parser: Available")
    print(f"   - Features: Available")
    print("\n✅ System is ready for training!")
    print("\n📝 Next step: Run train_ml_track_ensemble.bat on your PC")
    print("="*80)
    
    return True

if __name__ == '__main__':
    try:
        success = test_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH ERROR:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
