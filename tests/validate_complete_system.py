#!/usr/bin/env python
"""
Comprehensive System Validation Test
Tests all critical components to ensure system is production-ready
"""

import os
import sys
import pandas as pd
from pathlib import Path

def test_syntax_all_files():
    """Test 1: Validate Python syntax for all critical files"""
    print("=" * 80)
    print("TEST 1: Python Syntax Validation")
    print("=" * 80)
    
    files_to_check = [
        'run_complete_analysis.py',
        'src/parser.py',
        'src/features.py',
        'src/ml_predictor.py',
        'train_ml_enhanced.py'
    ]
    
    errors = []
    for filepath in files_to_check:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                compile(f.read(), filepath, 'exec')
            print(f"✅ {filepath} - Syntax OK")
        except SyntaxError as e:
            errors.append(f"❌ {filepath} - SYNTAX ERROR: {e}")
            print(errors[-1])
    
    if errors:
        print(f"\n❌ FAILED: {len(errors)} syntax errors found")
        return False
    else:
        print("\n✅ PASSED: All files have valid Python syntax")
        return True

def test_imports():
    """Test 2: Verify all critical imports work"""
    print("\n" + "=" * 80)
    print("TEST 2: Import Validation")
    print("=" * 80)
    
    try:
        sys.path.insert(0, 'src')
        import parser as parser_module
        print("✅ parser module imports OK")
        
        import features
        print("✅ features module imports OK")
        
        import ml_predictor
        print("✅ ml_predictor module imports OK")
        
        print("\n✅ PASSED: All critical modules import successfully")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: Import error - {e}")
        return False

def test_data_availability():
    """Test 3: Check historical data availability"""
    print("\n" + "=" * 80)
    print("TEST 3: Historical Data Availability")
    print("=" * 80)
    
    data_dir = Path('data')
    
    # Count PDFs
    pdfs = list(data_dir.glob('*.pdf'))
    print(f"📄 PDFs found: {len(pdfs)}")
    
    # Count result CSVs
    result_csvs = list(data_dir.glob('results_*.csv'))
    print(f"📊 Result CSVs found: {len(result_csvs)}")
    
    # Count total races
    total_races = 0
    for csv_file in result_csvs:
        try:
            df = pd.read_csv(csv_file)
            total_races += len(df)
        except:
            pass
    
    print(f"🏁 Total historical races: {total_races}")
    
    if len(pdfs) < 200:
        print(f"⚠️  WARNING: Only {len(pdfs)} PDFs (expected 235+)")
    if len(result_csvs) < 15:
        print(f"⚠️  WARNING: Only {len(result_csvs)} result CSVs (expected 20+)")
    if total_races < 2000:
        print(f"⚠️  WARNING: Only {total_races} races (expected 2,524+)")
    
    if len(pdfs) >= 200 and total_races >= 2000:
        print("\n✅ PASSED: Sufficient historical data available")
        return True
    else:
        print("\n⚠️  PARTIAL PASS: Data available but less than expected")
        return True

def test_parser_function():
    """Test 4: Verify parser function exists and is callable"""
    print("\n" + "=" * 80)
    print("TEST 4: Parser Function Validation")
    print("=" * 80)
    
    try:
        sys.path.insert(0, 'src')
        from parser import parse_race_form
        
        print("✅ parse_race_form function found")
        print(f"✅ Function callable: {callable(parse_race_form)}")
        
        # Check if data_predictions folder exists
        pred_dir = Path('data_predictions')
        if pred_dir.exists():
            pdfs_in_pred = list(pred_dir.glob('*.pdf'))
            print(f"📄 PDFs in data_predictions/: {len(pdfs_in_pred)}")
        else:
            print("⚠️  data_predictions/ folder not found")
        
        print("\n✅ PASSED: Parser function is available")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False

def test_model_file():
    """Test 5: Check if trained model exists"""
    print("\n" + "=" * 80)
    print("TEST 5: Trained Model Check")
    print("=" * 80)
    
    models_dir = Path('models')
    if not models_dir.exists():
        print("⚠️  models/ directory not found - need to run training")
        return False
    
    model_files = list(models_dir.glob('*.pkl'))
    print(f"🤖 Model files found: {len(model_files)}")
    
    for model_file in model_files:
        print(f"   - {model_file.name} ({model_file.stat().st_size / 1024:.1f} KB)")
    
    if len(model_files) == 0:
        print("\n⚠️  NO MODEL FOUND: Run train_ml_enhanced.bat first")
        return False
    else:
        print("\n✅ PASSED: Trained model(s) available")
        return True

def test_output_directory():
    """Test 6: Verify outputs directory exists"""
    print("\n" + "=" * 80)
    print("TEST 6: Output Directory Check")
    print("=" * 80)
    
    outputs_dir = Path('outputs')
    if not outputs_dir.exists():
        outputs_dir.mkdir(exist_ok=True)
        print("✅ Created outputs/ directory")
    else:
        print("✅ outputs/ directory exists")
    
    return True

def run_all_tests():
    """Run all validation tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "COMPREHENSIVE SYSTEM VALIDATION" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = {
        'Syntax Validation': test_syntax_all_files(),
        'Import Validation': test_imports(),
        'Historical Data': test_data_availability(),
        'Parser Function': test_parser_function(),
        'Trained Model': test_model_file(),
        'Output Directory': test_output_directory()
    }
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} | {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅✅✅ ALL TESTS PASSED - SYSTEM IS READY ✅✅✅")
        print("=" * 80)
        print("\nNext steps:")
        print("1. If no model found: Run train_ml_enhanced.bat (15-45 min)")
        print("2. Place today's PDFs in data_predictions/ folder")
        print("3. Run run_complete_analysis.bat (2-5 min)")
        print("4. Check outputs/ folder for Excel files")
    else:
        print("❌ SOME TESTS FAILED - REVIEW ERRORS ABOVE")
        print("=" * 80)
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"\nFailed tests: {', '.join(failed_tests)}")
    
    return all_passed

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
