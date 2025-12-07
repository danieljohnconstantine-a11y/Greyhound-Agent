"""
Demo: Hybrid ML + v4.4 Prediction System

Shows how to combine ML predictions with v4.4 rule-based scoring
for maximum accuracy on greyhound races.

Usage:
    python demo_ml_hybrid.py [pdf_file]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pdfplumber
from src.parser import parse_race_form
from src.features import compute_features
from src.scorer import score_race
from src.bet_worthy import detect_bet_worthy
from src.ml_predictor import GreyhoundMLPredictor
import pandas as pd

def demo_hybrid_prediction(pdf_file=None, model_path='models/greyhound_ml_v1.pkl'):
    """
    Demonstrate hybrid ML + v4.4 prediction on a race PDF.
    
    Args:
        pdf_file: Path to race PDF (optional, uses example if not provided)
        model_path: Path to trained ML model
    """
    print("=" * 80)
    print("🎯 HYBRID PREDICTION DEMO: ML + v4.4 Rule-Based System")
    print("=" * 80)
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"\n❌ ML model not found at: {model_path}")
        print(f"\n   Current directory: {os.getcwd()}")
        print(f"   Looking for model at: {os.path.abspath(model_path)}")
        print(f"\n   To train the ML model:")
        print(f"   - Windows: Double-click train_ml.bat")
        print(f"   - Command line: python train_ml_model.py")
        print(f"\n   The training will:")
        print(f"   1. Create the 'models' directory if needed")
        print(f"   2. Train on all PDFs and results CSVs in data/")
        print(f"   3. Save model to {model_path}")
        return
    
    # Load ML model
    print(f"\n📥 Loading ML model...")
    try:
        predictor = GreyhoundMLPredictor(model_path)
        print(f"   ✅ Model loaded successfully")
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        return
    
    # Get PDF file
    if pdf_file is None:
        # Use most recent PDF
        import glob
        pdfs = sorted(glob.glob('data/*0112form.pdf'))  # Dec 1 PDFs
        if not pdfs:
            pdfs = sorted(glob.glob('data/*form.pdf'))
        
        if not pdfs:
            print("\n❌ No PDF files found in data/ folder")
            return
        
        pdf_file = pdfs[0]
        print(f"\n📄 Using example PDF: {pdf_file}")
    
    # Parse PDF
    print(f"\n🔍 Parsing race data...")
    try:
        # Extract text from PDF
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Parse race form
        parsed_data = parse_race_form(text)
        if not parsed_data:
            print("   ❌ Failed to parse PDF")
            return
        
        print(f"   ✅ Found {len(parsed_data)} races")
    except Exception as e:
        print(f"   ❌ Error parsing PDF: {e}")
        return
    
    # Process first race as example
    race_info = parsed_data[0]
    track = race_info['track']
    race_num = race_info['race_number']
    df_race = race_info['race_data']
    
    print(f"\n📍 Analyzing: {track} Race {race_num}")
    print(f"   Dogs in race: {len(df_race)}")
    
    # Compute features
    print(f"\n⚙️  Computing v4.4 features...")
    df_race = compute_features(df_race)
    
    # Score with v4.4 system
    print(f"📊 Scoring with v4.4 rule-based system...")
    df_scored = score_race(df_race, track)
    rule_based_scores = df_scored['FinalScore']
    
    # Detect TIER0 with v4.4
    bet_worthy_info = detect_bet_worthy(df_scored)
    v4_4_tier = bet_worthy_info.get('tier', 'NONE')
    v4_4_recommended = bet_worthy_info.get('recommended_box')
    
    print(f"\n🎲 v4.4 PREDICTIONS:")
    print("-" * 80)
    print(f"   Tier: {v4_4_tier}")
    if v4_4_recommended:
        print(f"   Recommended: Box {v4_4_recommended}")
        top_dog = df_scored[df_scored['BoxDraw'] == v4_4_recommended].iloc[0]
        print(f"   Dog: {top_dog.get('DogName', 'Unknown')}")
        print(f"   Score: {rule_based_scores.max():.1f}")
        print(f"   Margin: {bet_worthy_info.get('margin_pct', 0):.1f}%")
    else:
        print(f"   Recommended: None (no TIER0 bet)")
    
    # Get ML predictions
    print(f"\n🤖 ML PREDICTIONS:")
    print("-" * 80)
    try:
        ml_confidence = predictor.predict_confidence(df_race)
        
        # Show top 3 ML picks
        top_3_ml = ml_confidence.nlargest(3)
        for idx, (dog_idx, conf) in enumerate(top_3_ml.items(), 1):
            dog = df_race.loc[dog_idx]
            print(f"   #{idx} Box {dog['BoxDraw']}: {dog.get('DogName', 'Unknown'):20} "
                  f"Confidence: {conf:.1f}%")
    except Exception as e:
        print(f"   ❌ Error getting ML predictions: {e}")
        return
    
    # Hybrid prediction
    print(f"\n🎯 HYBRID PREDICTION (ML + v4.4):")
    print("=" * 80)
    try:
        hybrid_result = predictor.hybrid_predict(
            df_race, 
            rule_based_scores,
            tier0_threshold=18,  # v4.4 TIER0 margin
            ml_threshold=75      # ML confidence threshold
        )
        
        print(f"\nDecision: ", end="")
        if hybrid_result['tier'] == 'HYBRID_TIER0':
            print(f"✅ BET (Both systems agree!)")
            print(f"\n💰 RECOMMENDED BET:")
            print(f"   Box: {hybrid_result['recommended_box']}")
            dog = df_race[df_race['BoxDraw'] == hybrid_result['recommended_box']].iloc[0]
            print(f"   Dog: {dog.get('DogName', 'Unknown')}")
            print(f"   v4.4 Score: {hybrid_result['rule_based_score']:.1f}")
            print(f"   v4.4 Margin: {hybrid_result['margin_pct']:.1f}%")
            print(f"   ML Confidence: {hybrid_result['ml_confidence']:.1f}%")
            print(f"\n   Expected win rate: 35-40% (vs 28-30% v4.4 alone)")
        else:
            print(f"⚠️  NO BET (Systems disagree or thresholds not met)")
            print(f"\n   v4.4 TIER0: {'✅' if v4_4_tier == 'TIER0' else '❌'}")
            print(f"   v4.4 Margin: {hybrid_result['margin_pct']:.1f}% (need 18%+)")
            print(f"   ML Confidence: {hybrid_result['ml_confidence']:.1f}% (need 75%+)")
            print(f"\n   Waiting for stronger signal...")
        
        # Show all predictions
        print(f"\n📊 DETAILED COMPARISON (All Dogs):")
        print("-" * 80)
        all_preds = hybrid_result['all_predictions']
        print(all_preds.to_string(index=False))
        
    except Exception as e:
        print(f"   ❌ Error in hybrid prediction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)
    
    print(f"\n📝 SUMMARY:")
    print(f"   v4.4 System: {'TIER0' if v4_4_tier == 'TIER0' else 'No bet'}")
    print(f"   ML System: {hybrid_result['ml_confidence']:.1f}% confidence")
    print(f"   Hybrid: {'BET' if hybrid_result['tier'] == 'HYBRID_TIER0' else 'NO BET'}")
    
    print(f"\n💡 KEY INSIGHT:")
    print(f"   Hybrid system is MORE SELECTIVE but MORE ACCURATE")
    print(f"   Only bets when both v4.4 AND ML strongly agree")
    print(f"   Target: 35-40% win rate (vs 12.5% random, 28-30% v4.4)")

if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else None
    demo_hybrid_prediction(pdf_file)
