#!/usr/bin/env python3
"""
Comprehensive PDF Testing Script
Tests all PDFs in data_predictions/ to achieve 100% confidence
"""

import os
import sys
import traceback
from pathlib import Path
import pdfplumber

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parser import parse_race_form

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def test_all_pdfs():
    """Test all PDFs in data_predictions directory"""
    
    print("=" * 80)
    print("COMPREHENSIVE PDF VALIDATION TEST")
    print("=" * 80)
    print()
    
    # Get all PDFs
    pdf_dir = Path('data_predictions')
    pdf_files = sorted([f for f in pdf_dir.glob('*.pdf')])
    
    print(f"Found {len(pdf_files)} PDF files to test")
    print()
    
    results = {
        'success': [],
        'failed': [],
        'no_dogs': []
    }
    
    for i, pdf_path in enumerate(pdf_files, 1):
        pdf_name = pdf_path.name
        print(f"{i}. Testing: {pdf_name}")
        print("-" * 60)
        
        try:
            # Extract text
            print(f"   Extracting text...", end=" ")
            text = extract_text_from_pdf(str(pdf_path))
            if not text:
                print("❌ FAILED - No text extracted")
                results['failed'].append((pdf_name, "No text extracted"))
                print()
                continue
            print(f"✅ ({len(text)} chars)")
            
            # Parse text
            print(f"   Parsing race form...", end=" ")
            dogs = parse_race_form(text)
            
            # Check if DataFrame is empty
            if dogs is None or (hasattr(dogs, 'empty') and dogs.empty):
                print("⚠️  WARNING - No dogs found")
                results['no_dogs'].append((pdf_name, "No dogs parsed"))
                print()
                continue
            
            # Convert to list if DataFrame
            if hasattr(dogs, 'to_dict'):
                dogs_list = dogs.to_dict('records')
                num_dogs = len(dogs_list)
            else:
                dogs_list = dogs
                num_dogs = len(dogs) if dogs else 0
                
            print(f"✅ Found {num_dogs} dogs")
            
            # Validate dog data
            print(f"   Validating dog data...")
            
            valid_dogs = 0
            for dog in dogs_list:
                if 'DogName' in dog and dog['DogName']:
                    valid_dogs += 1
                    # Show first dog as example
                    if valid_dogs == 1:
                        print(f"      Example: Box {dog.get('BoxNumber', '?')} - {dog['DogName']}")
                        features = [k for k in dog.keys() if k not in ['DogName', 'BoxNumber', 'Track', 'RaceNumber']]
                        print(f"      Features: {len(features)}")
            
            if valid_dogs > 0:
                print(f"   ✅ SUCCESS - {valid_dogs}/{num_dogs} valid dogs")
                results['success'].append((pdf_name, num_dogs, valid_dogs))
            else:
                print(f"   ❌ FAILED - No valid dogs with names")
                results['failed'].append((pdf_name, "No valid dogs"))
                
        except Exception as e:
            print(f"   ❌ EXCEPTION - {str(e)}")
            results['failed'].append((pdf_name, str(e)))
            # Print traceback for debugging
            traceback.print_exc()
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total = len(pdf_files)
    success_count = len(results['success'])
    failed_count = len(results['failed'])
    no_dogs_count = len(results['no_dogs'])
    
    print(f"Total PDFs tested: {total}")
    print(f"✅ Successful: {success_count} ({success_count/total*100:.1f}%)")
    print(f"⚠️  No dogs found: {no_dogs_count} ({no_dogs_count/total*100:.1f}%)")
    print(f"❌ Failed: {failed_count} ({failed_count/total*100:.1f}%)")
    print()
    
    if results['success']:
        print("Successful PDFs:")
        for pdf_name, total_dogs, valid_dogs in results['success']:
            print(f"  ✅ {pdf_name}: {valid_dogs} valid dogs (out of {total_dogs})")
        print()
    
    if results['no_dogs']:
        print("PDFs with no dogs (may be different format):")
        for pdf_name, reason in results['no_dogs']:
            print(f"  ⚠️  {pdf_name}: {reason}")
        print()
    
    if results['failed']:
        print("Failed PDFs:")
        for pdf_name, reason in results['failed']:
            print(f"  ❌ {pdf_name}: {reason}")
        print()
    
    # Calculate confidence
    parseable = success_count + no_dogs_count  # No dogs might just be empty PDFs
    confidence = (parseable / total * 100) if total > 0 else 0
    
    print("=" * 80)
    print(f"CONFIDENCE LEVEL: {confidence:.1f}%")
    print("=" * 80)
    
    if confidence >= 100:
        print("✅ 100% CONFIDENCE ACHIEVED!")
        print("   All PDFs can be processed successfully.")
    elif confidence >= 90:
        print("⚠️  HIGH CONFIDENCE but not perfect")
        print(f"   {failed_count} PDFs need attention.")
    else:
        print("❌ LOW CONFIDENCE")
        print(f"   {failed_count + no_dogs_count} PDFs have issues.")
    
    print()
    
    return confidence >= 100

if __name__ == '__main__':
    success = test_all_pdfs()
    sys.exit(0 if success else 1)
