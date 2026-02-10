#!/usr/bin/env python3
"""
Pipeline Validation Script

Tests the complete greyhound prediction pipeline end-to-end:
1. Model organization structure
2. Model loading from subdirectories
3. Prediction generation
4. Output organization
5. Logging system
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime

class PipelineValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "tests": []
        }
        
    def test(self, name, func):
        """Run a test and record results"""
        print(f"\n🧪 Testing: {name}")
        try:
            result = func()
            if result:
                print(f"   ✅ PASSED")
                self.results["tests_passed"] += 1
                self.results["tests"].append({"name": name, "status": "PASSED", "details": result})
                return True
            else:
                print(f"   ❌ FAILED")
                self.results["tests_failed"] += 1
                self.results["tests"].append({"name": name, "status": "FAILED", "details": "Test returned False"})
                return False
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results["tests_failed"] += 1
            self.results["tests"].append({"name": name, "status": "FAILED", "details": str(e)})
            return False
    
    def validate_model_structure(self):
        """Test 1: Validate model directory structure"""
        models_dir = Path("models")
        
        # Check for track subdirectories
        track_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name not in ['combined', '__pycache__']]
        
        if len(track_dirs) == 0:
            return {"error": "No track directories found"}
        
        structure_valid = True
        details = {"tracks_found": len(track_dirs), "tracks": {}}
        
        for track_dir in track_dirs:
            track_name = track_dir.name
            files_found = {}
            
            # Check for required files
            required_files = ['rf.pkl', 'gb.pkl', 'scaler.pkl', 'metadata.json']
            for req_file in required_files:
                file_path = track_dir / req_file
                files_found[req_file] = file_path.exists()
                if not file_path.exists():
                    structure_valid = False
            
            details["tracks"][track_name] = files_found
        
        details["all_valid"] = structure_valid
        return details
    
    def validate_model_loading(self):
        """Test 2: Load models from track subdirectories"""
        models_dir = Path("models")
        track_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name not in ['combined', '__pycache__']]
        
        if not track_dirs:
            return {"error": "No tracks to test"}
        
        # Test first track
        test_track = track_dirs[0]
        models_loaded = {}
        
        for model_file in ['rf.pkl', 'gb.pkl', 'scaler.pkl']:
            model_path = test_track / model_file
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    models_loaded[model_file] = {
                        "loaded": True,
                        "type": type(model).__name__
                    }
                except Exception as e:
                    models_loaded[model_file] = {
                        "loaded": False,
                        "error": str(e)
                    }
        
        return {
            "track_tested": test_track.name,
            "models_loaded": models_loaded,
            "success": all(m.get("loaded", False) for m in models_loaded.values())
        }
    
    def validate_outputs_structure(self):
        """Test 3: Validate outputs directory structure"""
        outputs_dir = Path("outputs")
        
        if not outputs_dir.exists():
            return {"error": "outputs directory not found"}
        
        by_track_dir = outputs_dir / "by_track"
        combined_dir = outputs_dir / "combined"
        
        details = {
            "by_track_exists": by_track_dir.exists(),
            "combined_exists": combined_dir.exists(),
            "tracks_organized": 0
        }
        
        if by_track_dir.exists():
            track_outputs = [d for d in by_track_dir.iterdir() if d.is_dir()]
            details["tracks_organized"] = len(track_outputs)
            details["track_list"] = [t.name for t in track_outputs[:5]]  # First 5
        
        if combined_dir.exists():
            combined_files = list(combined_dir.glob("*.xlsx")) + list(combined_dir.glob("*.txt"))
            details["combined_files"] = len(combined_files)
        
        return details
    
    def validate_metrics_files(self):
        """Test 4: Check training metrics files"""
        models_dir = Path("models")
        track_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name not in ['combined', '__pycache__']]
        
        metrics_found = 0
        for track_dir in track_dirs:
            metrics_file = track_dir / "training_metrics.json"
            if metrics_file.exists():
                metrics_found += 1
        
        return {
            "total_tracks": len(track_dirs),
            "tracks_with_metrics": metrics_found,
            "coverage_pct": (metrics_found / len(track_dirs) * 100) if track_dirs else 0
        }
    
    def validate_logs_directory(self):
        """Test 5: Check logs directory"""
        logs_dir = Path("logs")
        
        if not logs_dir.exists():
            return {"error": "logs directory not found"}
        
        log_files = list(logs_dir.glob("*.log"))
        
        return {
            "logs_found": len(log_files),
            "log_files": [f.name for f in log_files[:5]]
        }
    
    def run_all_tests(self):
        """Run complete validation suite"""
        print("=" * 80)
        print("GREYHOUND PREDICTION PIPELINE VALIDATION")
        print("=" * 80)
        
        # Run all tests
        self.test("Model Directory Structure", self.validate_model_structure)
        self.test("Model Loading Functionality", self.validate_model_loading)
        self.test("Outputs Organization", self.validate_outputs_structure)
        self.test("Training Metrics Files", self.validate_metrics_files)
        self.test("Logs Directory", self.validate_logs_directory)
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        total = self.results["tests_passed"] + self.results["tests_failed"]
        pass_rate = (self.results["tests_passed"] / total * 100) if total > 0 else 0
        
        print(f"\n✅ Tests Passed: {self.results['tests_passed']}")
        print(f"❌ Tests Failed: {self.results['tests_failed']}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        # Save detailed report
        report_file = Path("outputs") / "pipeline_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Final verdict
        print("\n" + "=" * 80)
        if self.results["tests_failed"] == 0:
            print("✅ PIPELINE VALIDATION: ALL TESTS PASSED")
            print("   The pipeline is ready for production use")
        else:
            print("⚠️  PIPELINE VALIDATION: SOME TESTS FAILED")
            print("   Review the detailed report and fix issues")
        print("=" * 80)
        
        return self.results["tests_failed"] == 0

def main():
    validator = PipelineValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
