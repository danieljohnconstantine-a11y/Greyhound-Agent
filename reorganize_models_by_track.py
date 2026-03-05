#!/usr/bin/env python3
"""
Reorganize Model Files by Track

This script reorganizes flat model files into track-specific subdirectories.
Converts: models/TRACKNAME_algorithm.pkl  
To: models/TRACKNAME/algorithm.pkl

Author: GitHub Copilot
Date: 2026-03-04
"""

import os
import shutil
import re
from pathlib import Path

def reorganize_models():
    """Reorganize models from flat structure to subdirectories."""
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print(f"❌ ERROR: {models_dir} directory not found!")
        return False
    
    print(f"📁 Scanning {models_dir}/ for model files...")
    
    # Find all pkl files (excluding config files)
    model_files = [f for f in models_dir.glob("*.pkl") if not f.name.startswith("config")]
    
    if not model_files:
        print("ℹ️  No model files found to reorganize")
        return True
    
    print(f"   Found {len(model_files)} model files")
    
    # Group files by track
    tracks = {}
    
    for file_path in model_files:
        filename = file_path.name
        
        # Pattern: TRACKNAME_algorithm.pkl or 'Track Name_algorithm.pkl'
        # Extract track name and algorithm
        match = re.match(r"^(.+?)_(rf|gb|xgb|scaler)\.pkl$", filename)
        
        if match:
            track_name = match.group(1)
            algorithm = match.group(2)
            
            if track_name not in tracks:
                tracks[track_name] = []
            tracks[track_name].append((filename, algorithm))
        else:
            print(f"   ⚠️  Skipping file with unexpected format: {filename}")
    
    if not tracks:
        print("❌ No valid track model files found!")
        return False
    
    print(f"\n📊 Found {len(tracks)} tracks to organize:")
    for track in sorted(tracks.keys()):
        print(f"   • {track} ({len(tracks[track])} files)")
    
    print(f"\n🔄 Reorganizing models into subdirectories...")
    
    success_count = 0
    error_count = 0
    
    for track_name, files in tracks.items():
        # Create track subdirectory
        track_dir = models_dir / track_name
        
        try:
            track_dir.mkdir(exist_ok=True)
            print(f"\n   📂 {track_name}/")
            
            # Move each file
            for old_filename, algorithm in files:
                old_path = models_dir / old_filename
                new_filename = f"{algorithm}.pkl"
                new_path = track_dir / new_filename
                
                # Move file
                shutil.move(str(old_path), str(new_path))
                print(f"      ✅ {old_filename} → {track_name}/{new_filename}")
                success_count += 1
                
        except Exception as e:
            print(f"      ❌ Error organizing {track_name}: {e}")
            error_count += 1
    
    print(f"\n" + "="*60)
    print(f"✅ Successfully reorganized: {success_count} files")
    if error_count > 0:
        print(f"❌ Errors: {error_count} files")
        print(f"="*60)
        return False
    
    print(f"="*60)
    
    # Verify structure
    print(f"\n🔍 Verifying new structure...")
    for track_name in sorted(tracks.keys()):
        track_dir = models_dir / track_name
        if track_dir.exists():
            files_in_dir = list(track_dir.glob("*.pkl"))
            print(f"   ✅ {track_name}/ contains {len(files_in_dir)} files")
        else:
            print(f"   ❌ {track_name}/ directory not found!")
            return False
    
    print(f"\n✅ Reorganization complete!")
    print(f"   Models now organized in: models/TRACK_NAME/")
    
    return True


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🏁 REORGANIZE MODELS BY TRACK")
    print("="*60)
    print()
    
    try:
        success = reorganize_models()
        
        if success:
            print("\n✅ SUCCESS: All models reorganized")
            sys.exit(0)
        else:
            print("\n❌ FAILED: Reorganization incomplete")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
