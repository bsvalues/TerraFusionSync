#!/usr/bin/env python3
"""
Quick benchmark test for TerraFusion GIS Export performance.

This script runs a simple comparison test to validate the benchmark suite
and demonstrate the performance differences between Python and Rust implementations.
"""

import sys
import subprocess
import json
from pathlib import Path

def run_quick_benchmark():
    """Run a quick benchmark test with sample data."""
    print("🧪 TerraFusion Quick Performance Test")
    print("=" * 50)
    
    # Test with small dataset first
    print("\n📊 Running quick test with 100 records...")
    
    try:
        # Run the benchmark
        result = subprocess.run([
            sys.executable, "benchmark/compare_gis.py",
            "--records", "100",
            "--format", "geojson",
            "--output", "benchmark/quick_test_results.csv"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Benchmark completed successfully!")
            print("\nResults summary:")
            print(result.stdout)
            
            # Check if results file was created
            results_file = Path("benchmark/quick_test_results.csv")
            if results_file.exists():
                print(f"📊 Detailed results saved to: {results_file}")
                
            summary_file = Path("benchmark/quick_test_results.md")
            if summary_file.exists():
                print(f"📄 Summary report saved to: {summary_file}")
                
        else:
            print("❌ Benchmark failed:")
            print(result.stderr)
            
            # Provide troubleshooting hints
            print("\n🔧 Troubleshooting tips:")
            print("1. Ensure TerraFusion API Gateway is running on port 5000")
            print("2. Check that GIS export endpoints are available")
            print("3. Verify database contains sample parcel data")
            
    except FileNotFoundError:
        print("❌ Python not found or benchmark script missing")
    except Exception as e:
        print(f"❌ Error running benchmark: {e}")

def check_services():
    """Check if required services are running."""
    print("🔍 Checking TerraFusion services...")
    
    import requests
    
    services = [
        ("API Gateway", "http://localhost:5000/health"),
        ("Sync Service", "http://localhost:8080/health"),
    ]
    
    all_healthy = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: Responding but unhealthy (status {response.status_code})")
                all_healthy = False
        except requests.exceptions.RequestException:
            print(f"❌ {name}: Not accessible")
            all_healthy = False
    
    return all_healthy

if __name__ == "__main__":
    print("🎯 TerraFusion Performance Benchmark Suite")
    print("This tool will test your GIS export performance improvements")
    print()
    
    # Check services first
    if check_services():
        print("\n🚀 All services are running! Starting benchmark...")
        run_quick_benchmark()
    else:
        print("\n⚠️  Some services are not running. Please start them first:")
        print("   - API Gateway: python main.py or gunicorn main:app")
        print("   - Sync Service: python run_syncservice_workflow_8080.py")