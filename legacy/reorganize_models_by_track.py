"""
Reorganize Track Ensemble Models into Track-Specific Subdirectories

This script reorganizes the flat model directory structure into track-specific subdirectories
for better organization and scalability.

Old structure:
    models/
        TRACK1_rf.pkl
        TRACK1_gb.pkl
        TRACK1_xgb.pkl
        TRACK1_scaler.pkl
        TRACK2_rf.pkl
        ...

New structure:
    models/
        TRACK1/
            rf.pkl
            gb.pkl
            xgb.pkl
            scaler.pkl
            metrics.json
        TRACK2/
            rf.pkl
            gb.pkl
            xgb.pkl
            scaler.pkl
            metrics.json
        ...
"""

import os
import shutil
import json
import pickle
from pathlib import Path

def reorganize_models():
    """Reorganize models from flat structure to track subdirectories"""
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("❌ models/ directory not found!")
        return
    
    # Find all track-specific model files
    model_files = list(models_dir.glob("*_*.pkl"))
    
    if not model_files:
        print("ℹ️  No track-specific models found to reorganize")
        return
    
    # Group files by track
    tracks = {}
    for file_path in model_files:
        filename = file_path.name
        
        # Skip config files
        if filename in ['config.pkl', 'ensemble_config.json']:
            continue
        
        # Extract track name (everything before last underscore)
        if '_' in filename:
            parts = filename.rsplit('_', 1)
            track_name = parts[0]
            model_type = parts[1].replace('.pkl', '')
            
            if track_name not in tracks:
                tracks[track_name] = []
            tracks[track_name].append((file_path, model_type))
    
    if not tracks:
        print("ℹ️  No track models found to reorganize")
        return
    
    print(f"\n📁 Found {len(tracks)} tracks with models to reorganize")
    print("=" * 80)
    
    reorganized_count = 0
    
    for track_name, files in sorted(tracks.items()):
        track_dir = models_dir / track_name
        track_dir.mkdir(exist_ok=True)
        
        print(f"\n🔄 Reorganizing {track_name}...")
        
        for old_path, model_type in files:
            new_path = track_dir / f"{model_type}.pkl"
            
            # Move file
            shutil.copy2(old_path, new_path)
            print(f"   ✅ {old_path.name} -> {track_name}/{new_path.name}")
            reorganized_count += 1
        
        # Create a metadata file
        metadata = {
            'track': track_name,
            'models': [model_type for _, model_type in files],
            'reorganized_date': str(Path(files[0][0]).stat().st_mtime)
        }
        
        metadata_path = track_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"   📝 Created metadata.json")
    
    print(f"\n" + "=" * 80)
    print(f"✅ Successfully reorganized {reorganized_count} model files into {len(tracks)} track directories")
    print(f"\n📂 New structure: models/TRACK_NAME/{{rf,gb,xgb,scaler}}.pkl")
    print(f"\nℹ️  Original files kept in models/ directory for backup")
    print(f"   You can safely delete them after verifying the new structure works.")

def update_config_file():
    """Update the config file to reflect new directory structure"""
    config_path = Path("models/config.pkl")
    
    if not config_path.exists():
        print("\nℹ️  No config.pkl found - skipping config update")
        return
    
    print("\n🔧 Updating config file...")
    
    try:
        with open(config_path, 'rb') as f:
            config = pickle.load(f)
        
        # Add directory structure info
        config['model_structure'] = 'track_subdirectories'
        config['model_path_template'] = 'models/{track}/{algorithm}.pkl'
        
        # Save updated config
        with open(config_path, 'wb') as f:
            pickle.dump(config, f)
        
        # Also save JSON version
        json_config_path = Path("models/ensemble_config.json")
        if json_config_path.exists():
            with open(json_config_path, 'r') as f:
                json_config = json.load(f)
            
            json_config['model_structure'] = 'track_subdirectories'
            json_config['model_path_template'] = 'models/{track}/{algorithm}.pkl'
            
            with open(json_config_path, 'w') as f:
                json.dump(json_config, f, indent=2)
        
        print("   ✅ Config files updated")
        
    except Exception as e:
        print(f"   ⚠️  Could not update config: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("REORGANIZING TRACK ENSEMBLE MODELS")
    print("=" * 80)
    
    reorganize_models()
    update_config_file()
    
    print("\n" + "=" * 80)
    print("✅ REORGANIZATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Verify new structure: ls -la models/*/")
    print("2. Test predictions with reorganized models")
    print("3. Delete old files if everything works: rm models/*_*.pkl")
    print()
