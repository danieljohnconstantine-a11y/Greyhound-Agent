"""
Organize Prediction Outputs by Track

This script reorganizes prediction outputs into track-specific subdirectories
and creates individual track prediction files.

Old structure:
    outputs/
        track_ensemble_predictions.xlsx  (all tracks in one file)
        track_ensemble_summary.txt        (all tracks in one file)

New structure:
    outputs/
        by_track/
            TRACK1/
                predictions.xlsx
                summary.txt
                details.json
            TRACK2/
                predictions.xlsx
                summary.txt
                details.json
        combined/
            all_tracks_predictions.xlsx
            all_tracks_summary.txt
"""

import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def organize_prediction_outputs():
    """Reorganize prediction outputs into track-specific directories"""
    
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        print("❌ outputs/ directory not found!")
        return
    
    # Check for the combined predictions file
    combined_xlsx = outputs_dir / "track_ensemble_predictions.xlsx"
    combined_summary = outputs_dir / "track_ensemble_summary.txt"
    
    if not combined_xlsx.exists():
        print("❌ track_ensemble_predictions.xlsx not found!")
        return
    
    print("\n" + "=" * 80)
    print("ORGANIZING PREDICTION OUTPUTS BY TRACK")
    print("=" * 80)
    
    # Create directory structure
    by_track_dir = outputs_dir / "by_track"
    combined_dir = outputs_dir / "combined"
    by_track_dir.mkdir(exist_ok=True)
    combined_dir.mkdir(exist_ok=True)
    
    # Read the combined predictions
    print("\n📖 Reading combined predictions file...")
    df = pd.read_excel(combined_xlsx)
    
    print(f"   ✅ Loaded {len(df)} predictions")
    print(f"   📊 Columns: {', '.join(df.columns.tolist())}")
    
    # Get unique tracks
    if 'Track' not in df.columns:
        print("❌ No 'Track' column found in predictions!")
        return
    
    tracks = df['Track'].unique()
    print(f"\n🎯 Found {len(tracks)} unique tracks")
    
    # Process each track
    for track in sorted(tracks):
        track_df = df[df['Track'] == track]
        track_dir = by_track_dir / track
        track_dir.mkdir(exist_ok=True)
        
        print(f"\n📁 Processing {track}...")
        print(f"   Races: {track_df['Race'].nunique() if 'Race' in track_df.columns else 'N/A'}")
        print(f"   Dogs: {len(track_df)}")
        
        # Save track-specific predictions
        track_xlsx = track_dir / "predictions.xlsx"
        track_df.to_excel(track_xlsx, index=False)
        print(f"   ✅ Saved predictions.xlsx ({len(track_df)} rows)")
        
        # Create summary
        summary_lines = []
        summary_lines.append(f"PREDICTIONS FOR {track}")
        summary_lines.append("=" * 60)
        summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append(f"Total Dogs: {len(track_df)}")
        
        if 'Race' in track_df.columns:
            summary_lines.append(f"Total Races: {track_df['Race'].nunique()}")
            summary_lines.append("")
            summary_lines.append("RACE-BY-RACE PREDICTIONS:")
            summary_lines.append("-" * 60)
            
            for race_num in sorted(track_df['Race'].unique()):
                race_df = track_df[track_df['Race'] == race_num]
                if 'Predicted_Probability' in race_df.columns:
                    top_dog = race_df.loc[race_df['Predicted_Probability'].idxmax()]
                    box = top_dog.get('Box', 'N/A')
                    dog_name = top_dog.get('DogName', 'N/A')
                    prob = top_dog.get('Predicted_Probability', 0)
                    summary_lines.append(f"Race {race_num}: Box {box} - {dog_name} ({prob:.1%})")
        
        # Save summary
        summary_path = track_dir / "summary.txt"
        with open(summary_path, 'w') as f:
            f.write('\n'.join(summary_lines))
        print(f"   ✅ Saved summary.txt")
        
        # Save detailed JSON
        details = {
            'track': track,
            'generated': datetime.now().isoformat(),
            'total_dogs': len(track_df),
            'total_races': int(track_df['Race'].nunique()) if 'Race' in track_df.columns else 0,
            'predictions': track_df.to_dict('records')
        }
        
        details_path = track_dir / "details.json"
        with open(details_path, 'w') as f:
            json.dump(details, f, indent=2, default=str)
        print(f"   ✅ Saved details.json")
    
    # Copy combined files to combined directory
    print(f"\n📦 Creating combined outputs...")
    import shutil
    
    if combined_xlsx.exists():
        shutil.copy2(combined_xlsx, combined_dir / "all_tracks_predictions.xlsx")
        print(f"   ✅ Saved all_tracks_predictions.xlsx")
    
    if combined_summary.exists():
        shutil.copy2(combined_summary, combined_dir / "all_tracks_summary.txt")
        print(f"   ✅ Saved all_tracks_summary.txt")
    
    print("\n" + "=" * 80)
    print("✅ ORGANIZATION COMPLETE")
    print("=" * 80)
    print(f"\n📂 Track-specific outputs: outputs/by_track/TRACK_NAME/")
    print(f"📂 Combined outputs: outputs/combined/")
    print(f"\nℹ️  Original files kept in outputs/ directory")

if __name__ == "__main__":
    organize_prediction_outputs()
