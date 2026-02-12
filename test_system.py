#!/usr/bin/env python3
"""
System Requirements Check for Greyhound-Agent

This script checks if your system meets all requirements to run the ML training pipeline.
Run this BEFORE downloading the full repository to ensure compatibility.

Usage:
    python3 test_system.py
    
Or run directly without downloading:
    curl -sSL https://raw.githubusercontent.com/.../test_system.py | python3
"""

import sys
import platform
import subprocess
import os

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"\n🐍 Python Version: {version_str}")
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ PASS (Minimum: 3.8)")
        return True
    else:
        print(f"   ❌ FAIL (Minimum: 3.8, Found: {version_str})")
        print(f"   💡 Upgrade Python: https://www.python.org/downloads/")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed and can be imported"""
    if import_name is None:
        import_name = package_name
    
    # Check if installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Extract version
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    print(f"📦 {package_name}: {version}")
                    break
            else:
                print(f"📦 {package_name}: installed")
            
            # Try importing
            try:
                __import__(import_name)
                print(f"   ✅ PASS (installed and importable)")
                return True
            except ImportError as e:
                print(f"   ⚠️  Installed but import failed: {e}")
                return False
        else:
            print(f"📦 {package_name}: NOT INSTALLED")
            print(f"   ❌ FAIL")
            print(f"   💡 Install: pip install {package_name}")
            return False
            
    except Exception as e:
        print(f"📦 {package_name}: Error checking - {e}")
        return False

def check_system_resources():
    """Check RAM and disk space"""
    print(f"\n💾 System Resources:")
    
    results = {'ram': False, 'disk': False}
    
    # Check RAM
    try:
        if platform.system() == "Linux":
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        ram_kb = int(line.split()[1])
                        ram_gb = ram_kb / (1024 ** 2)
                        print(f"   RAM: {ram_gb:.1f} GB")
                        if ram_gb >= 4:
                            print(f"   ✅ PASS (Recommended: 4+ GB)")
                            results['ram'] = True
                        else:
                            print(f"   ⚠️  LOW (Recommended: 4+ GB, you have {ram_gb:.1f} GB)")
                            print(f"   💡 Training may be slow with less than 4 GB RAM")
                            results['ram'] = True  # Still pass but warn
                        break
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(['sysctl', 'hw.memsize'], capture_output=True, text=True)
            if result.returncode == 0:
                ram_bytes = int(result.stdout.split(':')[1].strip())
                ram_gb = ram_bytes / (1024 ** 3)
                print(f"   RAM: {ram_gb:.1f} GB")
                if ram_gb >= 4:
                    print(f"   ✅ PASS (Recommended: 4+ GB)")
                    results['ram'] = True
                else:
                    print(f"   ⚠️  LOW (Recommended: 4+ GB)")
                    results['ram'] = True
        elif platform.system() == "Windows":
            try:
                import psutil
                ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                print(f"   RAM: {ram_gb:.1f} GB")
                if ram_gb >= 4:
                    print(f"   ✅ PASS (Recommended: 4+ GB)")
                    results['ram'] = True
                else:
                    print(f"   ⚠️  LOW (Recommended: 4+ GB)")
                    results['ram'] = True
            except ImportError:
                print(f"   ⚠️  Cannot check RAM (psutil not installed)")
                print(f"   💡 Check RAM manually: Task Manager > Performance > Memory")
                results['ram'] = True  # Pass but can't verify
        else:
            print(f"   ⚠️  Cannot check RAM on {platform.system()}")
            results['ram'] = True  # Pass but can't verify
    except Exception as e:
        print(f"   ⚠️  Error checking RAM: {e}")
        results['ram'] = True  # Pass but can't verify
    
    # Check disk space
    try:
        if platform.system() in ["Linux", "Darwin"]:
            stat = os.statvfs(os.path.expanduser('~'))
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            print(f"   Disk Free: {free_gb:.1f} GB")
            if free_gb >= 0.5:  # 500 MB
                print(f"   ✅ PASS (Need: 0.5+ GB)")
                results['disk'] = True
            else:
                print(f"   ❌ FAIL (Need: 0.5+ GB, you have {free_gb:.1f} GB)")
                print(f"   💡 Free up disk space before downloading")
        elif platform.system() == "Windows":
            try:
                import psutil
                disk = psutil.disk_usage(os.path.expanduser('~'))
                free_gb = disk.free / (1024 ** 3)
                print(f"   Disk Free: {free_gb:.1f} GB")
                if free_gb >= 0.5:
                    print(f"   ✅ PASS (Need: 0.5+ GB)")
                    results['disk'] = True
                else:
                    print(f"   ❌ FAIL (Need: 0.5+ GB)")
                    results['disk'] = True
            except ImportError:
                print(f"   ⚠️  Cannot check disk (psutil not installed)")
                results['disk'] = True
        else:
            print(f"   ⚠️  Cannot check disk on {platform.system()}")
            results['disk'] = True
    except Exception as e:
        print(f"   ⚠️  Error checking disk: {e}")
        results['disk'] = True
    
    return results['ram'] and results['disk']

def check_git():
    """Check if Git is installed"""
    print(f"\n🔧 Git:")
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   {version}")
            print(f"   ✅ PASS")
            return True
        else:
            print(f"   ❌ FAIL (Not installed)")
            print(f"   💡 Install Git: https://git-scm.com/downloads")
            return False
    except FileNotFoundError:
        print(f"   ❌ FAIL (Not found)")
        print(f"   💡 Install Git: https://git-scm.com/downloads")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def check_venv():
    """Check if virtual environment support exists"""
    print(f"\n🏗️  Virtual Environment:")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✅ PASS (venv module available)")
            return True
        else:
            print(f"   ❌ FAIL (venv module not found)")
            print(f"   💡 Install: sudo apt install python3-venv")
            return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def main():
    """Run all system checks"""
    print_header("🔍 GREYHOUND-AGENT SYSTEM REQUIREMENTS CHECK")
    
    print(f"\n📊 System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {sys.executable}")
    
    # Track results
    all_passed = True
    
    # Check Python version
    if not check_python_version():
        all_passed = False
    
    # Check required packages
    print_header("📦 REQUIRED PACKAGES")
    packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('xgboost', 'xgboost'),
        ('pdfplumber', 'pdfplumber'),
        ('openpyxl', 'openpyxl'),
    ]
    
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            all_passed = False
    
    # Check system resources
    print_header("💾 SYSTEM RESOURCES")
    if not check_system_resources():
        all_passed = False
    
    # Check Git
    if not check_git():
        all_passed = False
    
    # Check venv
    if not check_venv():
        all_passed = False
    
    # Print summary
    print_header("📋 SUMMARY")
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED!")
        print("\n🎉 Your system is ready to run Greyhound-Agent!")
        print("\n📥 Next Steps:")
        print("   1. Download the repository (see DOWNLOAD_INSTRUCTIONS.md)")
        print("   2. Follow setup guide (see UBUNTU_VENV_GUIDE.md or WSL_QUICK_START.md)")
        print("   3. Run training (python train_ml_track_ensemble.py)")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\n💡 Fix the issues above before downloading.")
        print("\n📚 Resources:")
        print("   - Python: https://www.python.org/downloads/")
        print("   - Git: https://git-scm.com/downloads")
        print("   - Packages: pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl")
        print("\n🔄 Rerun this script after fixing issues.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
