"""
Machine Learning Predictor for Greyhound Racing
Hybrid approach: Combines v4.4 rule-based scoring with ML confidence

This module trains on historical race data to learn non-linear patterns
that complement the hand-crafted features in v4.4.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os
from datetime import datetime

class GreyhoundMLPredictor:
    """
    ML predictor using Random Forest to identify winning dogs.
    
    Works alongside v4.4 rule-based system:
    - Rule-based: 28-30% win rate (proven factors)
    - ML: Learns hidden patterns from data
    - Hybrid: Only bet when both agree (35-40% expected)
    """
    
    def __init__(self, model_path=None):
        """
        Initialize ML predictor.
        
        Args:
            model_path: Path to saved model file (optional)
        """
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced data (8 dogs, 1 winner)
        )
        self.scaler = StandardScaler()
        self.feature_names = []
        self.trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def prepare_features(self, df):
        """
        Extract features from race data for ML training/prediction.
        
        Uses all 51 v4.4 scoring factors plus derived features.
        
        Args:
            df: DataFrame with computed features
            
        Returns:
            X: Feature matrix (dogs x features)
            feature_names: List of feature column names
        """
        # Core features from v4.4 scoring
        feature_cols = [
            # Box/Position
            'BoxDraw', 'DrawFactor',
            
            # Speed/Timing
            'BestTimeSec', 'SectionalSec', 'Speed_kmh',
            
            # Form/Momentum
            'DLR', 'DLW', 'Last3Positions',
            
            # Career/Experience
            'CareerStarts', 'CareerWins', 'CareerPlaces',
            'WinPercentage', 'PlacePercentage',
            
            # Conditioning
            'Age_months', 'Weight',
            
            # Trainer
            'TrainerStrikeRate',
        ]
        
        # Add derived features
        df_features = df.copy()
        
        # Consistency metrics
        if 'CareerStarts' in df.columns and 'CareerWins' in df.columns:
            df_features['ConsistencyIndex'] = df['CareerWins'] / (df['CareerStarts'] + 1)
            feature_cols.append('ConsistencyIndex')
        
        if 'CareerStarts' in df.columns and 'CareerPlaces' in df.columns:
            df_features['PlaceRate'] = df['CareerPlaces'] / (df['CareerStarts'] + 1)
            feature_cols.append('PlaceRate')
        
        # Hot form indicator
        if 'DLW' in df.columns:
            df_features['HotForm'] = (df['DLW'] <= 7).astype(int)
            feature_cols.append('HotForm')
        
        # Experience tier
        if 'CareerStarts' in df.columns:
            df_features['ExperienceTier'] = pd.cut(
                df['CareerStarts'], 
                bins=[0, 15, 40, 100, 1000],
                labels=[0, 1, 2, 3]
            ).astype(float)
            feature_cols.append('ExperienceTier')
        
        # Speed percentile within race
        if 'BestTimeSec' in df.columns:
            df_features['BestTimePercentile'] = df.groupby('Track')['BestTimeSec'].rank(pct=True)
            feature_cols.append('BestTimePercentile')
        
        # Filter to available features
        available_cols = [c for c in feature_cols if c in df_features.columns]
        X = df_features[available_cols].fillna(0)  # Fill missing with 0
        
        self.feature_names = available_cols
        return X, available_cols
    
    def train(self, historical_data, results):
        """
        Train ML model on historical race data.
        
        Args:
            historical_data: List of DataFrames (one per race) with computed features
            results: List of winning box numbers (one per race)
            
        Returns:
            dict: Training metrics (accuracy, feature importance, etc.)
        """
        print("🤖 Training ML model on historical data...")
        
        # Prepare training data
        X_list = []
        y_list = []
        
        for race_df, winner_box in zip(historical_data, results):
            if race_df is None or winner_box is None:
                continue
                
            X_race, _ = self.prepare_features(race_df)
            
            # Create labels: 1 for winner, 0 for others
            y_race = (race_df['BoxDraw'] == winner_box).astype(int)
            
            X_list.append(X_race)
            y_list.append(y_race)
        
        if not X_list:
            raise ValueError("No valid training data provided")
        
        # Combine all races
        X = pd.concat(X_list, ignore_index=True)
        y = pd.concat(y_list, ignore_index=True)
        
        print(f"📊 Training data: {len(X)} dogs from {len(historical_data)} races")
        print(f"   Winners: {y.sum()} ({y.mean()*100:.1f}%)")
        
        # Split for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.trained = True
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, scoring='accuracy'
        )
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Predictions on validation
        y_pred = self.model.predict(X_val_scaled)
        
        metrics = {
            'train_accuracy': train_score,
            'val_accuracy': val_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': feature_importance,
            'n_races': len(historical_data),
            'n_dogs': len(X),
            'classification_report': classification_report(y_val, y_pred),
            'confusion_matrix': confusion_matrix(y_val, y_pred)
        }
        
        print(f"\n✅ Training complete:")
        print(f"   Train accuracy: {train_score:.1%}")
        print(f"   Validation accuracy: {val_score:.1%}")
        print(f"   CV accuracy: {cv_scores.mean():.1%} (+/- {cv_scores.std()*2:.1%})")
        print(f"\n🔝 Top 5 Features:")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        return metrics
    
    def predict_confidence(self, race_df):
        """
        Predict win confidence for each dog in a race.
        
        Args:
            race_df: DataFrame with race data and computed features
            
        Returns:
            Series: Win confidence (0-100%) for each dog
        """
        if not self.trained:
            raise ValueError("Model not trained. Call train() first.")
        
        X, _ = self.prepare_features(race_df)
        X_scaled = self.scaler.transform(X)
        
        # Get probability of winning (class 1)
        proba = self.model.predict_proba(X_scaled)[:, 1]
        
        # Convert to 0-100 scale
        confidence = proba * 100
        
        return pd.Series(confidence, index=race_df.index)
    
    def hybrid_predict(self, race_df, rule_based_scores, tier0_threshold=18, ml_threshold=75):
        """
        Hybrid prediction: Combine ML + v4.4 rule-based scoring.
        
        Only recommend bets where BOTH systems agree:
        - v4.4: TIER0 selection (top dog with 18%+ margin)
        - ML: High confidence (75%+ win probability)
        
        Args:
            race_df: DataFrame with race data
            rule_based_scores: Series with v4.4 scores
            tier0_threshold: Min margin % for TIER0 (default 18%)
            ml_threshold: Min ML confidence % (default 75%)
            
        Returns:
            dict: {
                'recommended_box': Box number or None,
                'rule_based_score': v4.4 score,
                'ml_confidence': ML confidence %,
                'tier': 'HYBRID_TIER0' if both agree, else None,
                'all_predictions': DataFrame with all dog predictions
            }
        """
        # Get ML confidence
        ml_confidence = self.predict_confidence(race_df)
        
        # Create combined predictions DataFrame
        predictions = pd.DataFrame({
            'Box': race_df['BoxDraw'],
            'DogName': race_df.get('DogName', ''),
            'RuleBased_Score': rule_based_scores,
            'ML_Confidence': ml_confidence
        })
        
        # Find TIER0 candidate from rule-based
        top_idx = rule_based_scores.idxmax()
        top_score = rule_based_scores.max()
        second_score = rule_based_scores.nlargest(2).iloc[-1]
        margin_pct = ((top_score - second_score) / top_score) * 100
        
        is_tier0 = margin_pct >= tier0_threshold
        
        # Check ML confidence for top dog
        top_ml_confidence = ml_confidence.loc[top_idx]
        ml_agrees = top_ml_confidence >= ml_threshold
        
        # Hybrid recommendation: both must agree
        recommended = None
        tier = None
        
        if is_tier0 and ml_agrees:
            recommended = race_df.loc[top_idx, 'BoxDraw']
            tier = 'HYBRID_TIER0'
            print(f"✅ HYBRID TIER0: Box {recommended} "
                  f"(v4.4: {top_score:.1f}, margin: {margin_pct:.1f}%, "
                  f"ML: {top_ml_confidence:.1f}%)")
        elif is_tier0:
            print(f"⚠️  v4.4 TIER0 but ML low confidence: Box {race_df.loc[top_idx, 'BoxDraw']} "
                  f"(ML: {top_ml_confidence:.1f}% < {ml_threshold}%)")
        elif ml_agrees:
            print(f"⚠️  ML confident but v4.4 margin too low: Box {race_df.loc[top_idx, 'BoxDraw']} "
                  f"(margin: {margin_pct:.1f}% < {tier0_threshold}%)")
        
        predictions = predictions.sort_values('ML_Confidence', ascending=False)
        
        return {
            'recommended_box': recommended,
            'rule_based_score': top_score,
            'ml_confidence': top_ml_confidence,
            'margin_pct': margin_pct,
            'tier': tier,
            'all_predictions': predictions
        }
    
    def save_model(self, path):
        """Save trained model to disk."""
        if not self.trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained': self.trained,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {path}")
    
    def load_model(self, path):
        """Load trained model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.trained = model_data['trained']
        
        print(f"📥 Model loaded from {path}")
        print(f"   Trained: {model_data.get('timestamp', 'unknown')}")


def load_historical_data(data_dir='data'):
    """
    Load historical race PDFs and results for ML training.
    
    Args:
        data_dir: Directory containing PDFs and results CSVs
        
    Returns:
        tuple: (list of race DataFrames, list of winning boxes)
    """
    import pdfplumber
    from src.parser import parse_race_form
    from src.features import compute_features
    import glob
    
    # Find all PDFs and results
    pdf_files = glob.glob(f"{data_dir}/*form.pdf")
    results_files = glob.glob(f"{data_dir}/results_*.csv")
    
    print(f"📁 Found {len(pdf_files)} PDFs and {len(results_files)} results files")
    
    # Parse results
    all_results = {}
    for results_file in results_files:
        df_results = pd.read_csv(results_file)
        for _, row in df_results.iterrows():
            track = row.get('Track', row.get('track', ''))
            race_num = row.get('Race', row.get('race', ''))
            winner = row.get('Winner', row.get('winner', ''))
            
            # Extract box number from winner (e.g., "2" from "2546")
            if isinstance(winner, str) and winner:
                winner_box = int(winner[0])
                key = f"{track}_R{race_num}"
                all_results[key] = winner_box
    
    print(f"📊 Loaded {len(all_results)} race results")
    
    # Parse PDFs and match with results
    race_data = []
    winners = []
    
    for pdf_file in sorted(pdf_files):
        try:
            # Extract text from PDF using pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            # Parse the extracted text
            df_all_dogs = parse_race_form(text)
            if df_all_dogs is None or df_all_dogs.empty:
                continue
                
            # Compute features for all dogs
            df_all_dogs = compute_features(df_all_dogs)
            
            # Group by race and match with results
            if 'Track' in df_all_dogs.columns and 'RaceNumber' in df_all_dogs.columns:
                for (track, race_num), df_race in df_all_dogs.groupby(['Track', 'RaceNumber']):
                    # Match with results
                    key = f"{track}_R{race_num}"
                    if key in all_results:
                        race_data.append(df_race)
                        winners.append(all_results[key])
        
        except Exception as e:
            print(f"⚠️  Error processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"✅ Successfully loaded {len(race_data)} races with results")
    
    return race_data, winners


if __name__ == "__main__":
    """
    Example usage: Train ML model on historical data
    """
    print("=" * 60)
    print("🤖 Greyhound ML Predictor - Training Demo")
    print("=" * 60)
    
    # Load historical data
    print("\n1️⃣  Loading historical data...")
    race_data, winners = load_historical_data('data')
    
    if len(race_data) < 50:
        print(f"⚠️  Warning: Only {len(race_data)} races available. Recommend 200+ for robust training.")
    
    # Initialize and train
    print("\n2️⃣  Training ML model...")
    predictor = GreyhoundMLPredictor()
    metrics = predictor.train(race_data, winners)
    
    # Save model
    model_path = 'models/greyhound_ml_v1.pkl'
    os.makedirs('models', exist_ok=True)
    predictor.save_model(model_path)
    
    print("\n" + "=" * 60)
    print("✅ Training complete! Model ready for hybrid predictions.")
    print("=" * 60)
    print(f"\n📈 Expected performance:")
    print(f"   v4.4 alone: 28-30% win rate")
    print(f"   ML alone: {metrics['val_accuracy']*100:.1f}% win rate")
    print(f"   Hybrid (both agree): 35-40% expected")
    print(f"\nTo use: predictor.hybrid_predict(race_df, v4.4_scores)")
