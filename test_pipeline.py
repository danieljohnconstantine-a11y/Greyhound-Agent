"""
Test script to run predictions on specific PDFs
This tests SALE and WENTWORTH PARK models specifically
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import parse_race_form
from src.features import compute_features
import pandas as pd
import numpy as np
import pickle
import pdfplumber
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def load_track_ensemble(track_name, models_dir="models"):
    """Load all ensemble models for a specific track."""
    config_path = os.path.join(models_dir, "config.pkl")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ensemble configuration not found: {config_path}")
    
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    # Check if this track has models
    if track_name not in config['tracks']:
        return None, None, config
    
    # Load models from subdirectory
    track_dir = os.path.join(models_dir, track_name)
    
    models = {}
    for alg in config['algorithms']:
        model_path = os.path.join(track_dir, f"{alg}.pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                models[alg] = pickle.load(f)
    
    # Load scaler
    scaler_path = os.path.join(track_dir, "scaler.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
    else:
        scaler = None
    
    return models, scaler, config

def predict_with_ensemble(df, models, scaler, feature_cols, ensemble_weights):
    """Generate ensemble predictions for a race."""
    # Extract features and fill missing with 0
    X = df[feature_cols].fillna(0)
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Get predictions from each algorithm
    all_predictions = []
    individual_predictions = {}
    used_weights = []
    
    for alg, model in models.items():
        pred_proba = model.predict_proba(X_scaled)[:, 1]
        individual_predictions[alg] = pred_proba
        weight = ensemble_weights.get(alg, 1.0 / len(models))
        all_predictions.append(pred_proba * weight)
        used_weights.append(weight)
    
    # Normalize weights and compute weighted average
    total_weight = sum(used_weights)
    ensemble_pred = np.sum(all_predictions, axis=0) / total_weight
    
    return ensemble_pred, individual_predictions

def test_pdf(pdf_file, track_name):
    """Test prediction on a specific PDF file."""
    print("\n" + "=" * 80)
    print(f"Testing: {os.path.basename(pdf_file)}")
    print(f"Track: {track_name}")
    print("=" * 80)
    
    # Extract text
    print("\n1. Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(pdf_file)
    print(f"   ✓ Extracted {len(pdf_text)} characters")
    
    # Parse PDF
    print("\n2. Parsing race form...")
    race_df = parse_race_form(pdf_text)
    if race_df is None or len(race_df) == 0:
        print("   ✗ Failed to parse PDF")
        return None
    print(f"   ✓ Parsed {len(race_df)} dogs")
    
    # Compute features
    print("\n3. Computing features...")
    race_df = compute_features(race_df)
    print(f"   ✓ Computed features - {len(race_df.columns)} columns")
    
    # Load models
    print(f"\n4. Loading {track_name} models...")
    models, scaler, config = load_track_ensemble(track_name)
    if models is None:
        print(f"   ✗ No models found for {track_name}")
        return None
    print(f"   ✓ Loaded {len(models)} models: {', '.join(models.keys())}")
    
    # Make predictions
    print("\n5. Generating predictions...")
    feature_cols = config['feature_cols']
    ensemble_weights = config.get('ensemble_weights', {})
    
    ensemble_pred, individual_preds = predict_with_ensemble(
        race_df, models, scaler, feature_cols, ensemble_weights
    )
    
    # Add predictions to dataframe
    race_df['ML_Confidence'] = ensemble_pred
    for alg, preds in individual_preds.items():
        race_df[f'{alg.upper()}_Pred'] = preds
    
    # Sort by confidence
    race_df = race_df.sort_values('ML_Confidence', ascending=False)
    
    # Display results
    print("\n" + "=" * 80)
    print("PREDICTION RESULTS")
    print("=" * 80)
    
    display_cols = ['DogName', 'Box', 'ML_Confidence', 'RF_Pred', 'GB_Pred', 'XGB_Pred']
    available_cols = [col for col in display_cols if col in race_df.columns]
    
    result_df = race_df[available_cols].copy()
    
    # Format for display
    if 'ML_Confidence' in result_df.columns:
        result_df['ML_Confidence'] = result_df['ML_Confidence'].apply(lambda x: f"{x:.3f}")
    if 'RF_Pred' in result_df.columns:
        result_df['RF_Pred'] = result_df['RF_Pred'].apply(lambda x: f"{x:.3f}")
    if 'GB_Pred' in result_df.columns:
        result_df['GB_Pred'] = result_df['GB_Pred'].apply(lambda x: f"{x:.3f}")
    if 'XGB_Pred' in result_df.columns:
        result_df['XGB_Pred'] = result_df['XGB_Pred'].apply(lambda x: f"{x:.3f}")
    
    print(result_df.to_string(index=False))
    print("=" * 80)
    
    print("\n✓ Predictions completed successfully!")
    print(f"  - Ensemble ML applied to each of {len(race_df)} dogs individually")
    print(f"  - Used 3 algorithms: RF, GB, XGBoost")
    print(f"  - Track-specific models from models/{track_name}/")
    
    return race_df

def main():
    print("=" * 80)
    print("ML PIPELINE TEST - SPECIFIC PDFS")
    print("=" * 80)
    print("\nTesting prediction pipeline with:")
    print("  - SALEG0102form.pdf (SALE track)")
    print("  - WENPG2901form.pdf (WENTWORTH PARK track)")
    print("=" * 80)
    
    # Test SALE
    sale_result = test_pdf("data_predictions/SALEG0102form.pdf", "SALE")
    
    # Test WENTWORTH PARK
    wentworth_result = test_pdf("data_predictions/WENPG2901form.pdf", "WENTWORTH PARK")
    
    # Save combined results
    if sale_result is not None or wentworth_result is not None:
        print("\n" + "=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)
        
        all_results = []
        if sale_result is not None:
            sale_result['Track'] = 'SALE'
            sale_result['PDF'] = 'SALEG0102form.pdf'
            all_results.append(sale_result)
        if wentworth_result is not None:
            wentworth_result['Track'] = 'WENTWORTH PARK'
            wentworth_result['PDF'] = 'WENPG2901form.pdf'
            all_results.append(wentworth_result)
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            
            # Create output directory if needed
            os.makedirs('outputs', exist_ok=True)
            
            # Save to Excel
            output_file = 'outputs/pipeline_test_results.xlsx'
            combined_df.to_excel(output_file, index=False)
            print(f"\n✓ Saved results to: {output_file}")
            
            # Save summary
            summary_file = 'outputs/pipeline_test_summary.txt'
            with open(summary_file, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("ML PIPELINE TEST RESULTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nPDFs Tested:\n")
                f.write(f"  - SALEG0102form.pdf (SALE track)\n")
                f.write(f"  - WENPG2901form.pdf (WENTWORTH PARK track)\n")
                f.write(f"\nResults:\n")
                if sale_result is not None:
                    f.write(f"  ✓ SALE: {len(sale_result)} dogs predicted\n")
                if wentworth_result is not None:
                    f.write(f"  ✓ WENTWORTH PARK: {len(wentworth_result)} dogs predicted\n")
                f.write(f"\nTotal dogs with predictions: {len(combined_df)}\n")
                f.write(f"\nModels Used:\n")
                f.write(f"  - Random Forest (RF)\n")
                f.write(f"  - Gradient Boosting (GB)\n")
                f.write(f"  - XGBoost (XGB)\n")
                f.write(f"\nML applied individually to each dog: YES\n")
                f.write(f"Track-specific models used: YES\n")
                f.write("\n" + "=" * 80 + "\n")
            
            print(f"✓ Saved summary to: {summary_file}")
            
            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            print(f"\nTotal predictions: {len(combined_df)} dogs")
            print("ML applied individually to each dog: ✓")
            print("Track-specific models used: ✓")
            print("\nOutput files:")
            print(f"  - {output_file}")
            print(f"  - {summary_file}")
            
            return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
