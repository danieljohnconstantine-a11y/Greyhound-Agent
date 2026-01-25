"""
Quick Test Training - 3 Tracks
Tests maiden race fixes with Cannington, Dubbo, and Wentworth Park
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Run the full training script with test data directory
print("=" * 60)
print("QUICK TEST TRAINING - 3 TRACKS")
print("=" * 60)
print()
print("Testing tracks:")
print("  1. Cannington")
print("  2. Dubbo") 
print("  3. Wentworth Park")
print()
print("=" * 60)
print()
print("Starting training...")
print()
print("WATCH FOR THESE MESSAGES:")
print("  [WARNING] MAIDEN RACE - Using CareerStarts for differentiation")
print("  [WARNING] MAIDEN RACE (DLW='Mdn') - neutral DLWFactor")
print()
print("=" * 60)
print()

try:
    # Import after path setup
    from src.ml_predictor import load_historical_data_hybrid
    from src.features import compute_features
    import pandas as pd
    import numpy as np
    import pickle
    import json
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load test data
    pdf_dir = 'data_test'
    csv_dir = 'data_test'
    output_dir = 'models/track_ensemble_test'
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Loading historical data...")
    historical_data = load_historical_data_hybrid(pdf_dir=pdf_dir, csv_dir=csv_dir)
    
    if not historical_data:
        print("[ERROR] No historical data found!")
        sys.exit(1)
    
    logger.info(f"Loaded {len(historical_data)} races")
    
    # Group by track
    tracks = {}
    for race in historical_data:
        track = race.get('track', 'Unknown')
        if track not in tracks:
            tracks[track] = []
        tracks[track].append(race)
    
    logger.info(f"Found {len(tracks)} tracks: {list(tracks.keys())}")
    
    # Train a simple model for each track
    config = {'tracks': {}, 'ensemble_weights': [1.0/3, 1.0/3, 1.0/3]}
    
    for track, track_races in tracks.items():
        logger.info(f"Training {track} ensemble...")
        
        # Prepare training data
        X_list = []
        y_list = []
        
        for race in track_races:
            if 'dogs' not in race or 'winner' not in race:
                continue
            
            # Build features
            df = pd.DataFrame(race['dogs'])
            feature_matrix = compute_features(df)
            
            if feature_matrix is None or len(feature_matrix) == 0:
                continue
            
            X_list.append(feature_matrix)
            
            # Create labels
            winner_box = race['winner']
            y = (feature_matrix['Box'] == winner_box).astype(int)
            y_list.append(y)
        
        if not X_list:
            logger.warning(f"No training data for {track}")
            continue
        
        # Combine all races
        X = pd.concat(X_list, ignore_index=True)
        y = pd.concat(y_list, ignore_index=True)
        
        # Remove non-numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X_numeric = X[numeric_cols].fillna(0)
        
        logger.info(f"Training with {len(X_numeric)} samples, {len(numeric_cols)} features")
        
        # Train a simple RF model
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        rf_model.fit(X_numeric, y)
        
        accuracy = rf_model.score(X_numeric, y)
        logger.info(f"[SUCCESS] {track} - Accuracy: {accuracy:.1%}")
        
        # Save model
        model_path = os.path.join(output_dir, f"{track}_rf.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': rf_model,
                'features': list(numeric_cols),
                'scaler': None
            }, f)
        
        config['tracks'][track] = {
            'models': [f"{track}_rf.pkl"],
            'features': list(numeric_cols)
        }
    
    # Save config
    config_path = os.path.join(output_dir, 'ensemble_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also save as pickle for compatibility
    config_pkl_path = os.path.join(output_dir, 'config.pkl')
    with open(config_pkl_path, 'wb') as f:
        pickle.dump(config, f)
    
    print()
    print("=" * 60)
    print("[SUCCESS] TEST TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print(f"Trained {len(config['tracks'])} track models")
    print(f"Models saved to: {output_dir}/")
    print()
    
except Exception as e:
    print()
    print("=" * 60)
    print("[ERROR] ERROR DURING TRAINING")
    print("=" * 60)
    print()
    print(f"Error: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
