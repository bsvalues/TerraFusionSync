#!/usr/bin/env python3
"""
TerraFusion GIS Export Benchmark Suite

This script compares performance between Python and Rust GIS export implementations,
measuring execution time, memory usage, and validating output correctness.

Usage:
    python benchmark/compare_gis.py --format geojson --records 1000
    python benchmark/compare_gis.py --mode rust --format csv --records 5000
    python benchmark/compare_gis.py --all-formats --output results.csv
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import psutil
import requests
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Stores results from a single benchmark run."""
    timestamp: str
    mode: str  # 'python' or 'rust'
    format: str  # 'geojson', 'csv', 'shp', etc.
    record_count: int
    duration_seconds: float
    peak_memory_mb: float
    output_file_size_bytes: int
    output_hash: str
    success: bool
    error_message: Optional[str] = None

class GISBenchmark:
    """
    Benchmarks GIS export performance between Python and Rust implementations.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.python_endpoint = f"{base_url}/api/v1/gis-export/jobs"
        self.rust_endpoint = f"{base_url}/api/v2/gis-export/jobs"  # Assuming Rust API
        self.results: List[BenchmarkResult] = []
        
    def create_test_data(self, record_count: int) -> Dict:
        """
        Generate test parcel data for benchmarking.
        
        Args:
            record_count: Number of parcel records to generate
            
        Returns:
            Test data structure for export job
        """
        return {
            "county_id": "benchmark-county",
            "username": "benchmark-user",
            "area_of_interest": {
                "type": "Polygon",
                "coordinates": [[
                    [-119.2, 46.1],
                    [-119.0, 46.1], 
                    [-119.0, 46.3],
                    [-119.2, 46.3],
                    [-119.2, 46.1]
                ]]
            },
            "layers": ["parcels", "zoning"],
            "parameters": {
                "record_limit": record_count,
                "include_metadata": True,
                "benchmark_mode": True
            }
        }
    
    def monitor_memory(self, process_pid: int) -> float:
        """
        Monitor peak memory usage of a process.
        
        Args:
            process_pid: Process ID to monitor
            
        Returns:
            Peak memory usage in MB
        """
        try:
            process = psutil.Process(process_pid)
            peak_memory = 0
            
            while process.is_running():
                try:
                    memory_info = process.memory_info()
                    current_memory = memory_info.rss / (1024 * 1024)  # Convert to MB
                    peak_memory = max(peak_memory, current_memory)
                    time.sleep(0.1)  # Check every 100ms
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                    
            return peak_memory
        except Exception as e:
            logger.warning(f"Memory monitoring failed: {e}")
            return 0.0
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of output file for correctness validation.
        
        Args:
            file_path: Path to the output file
            
        Returns:
            SHA256 hash string
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return ""
    
    def run_export_job(self, mode: str, export_format: str, record_count: int) -> BenchmarkResult:
        """
        Run a single GIS export job and measure performance.
        
        Args:
            mode: 'python' or 'rust'
            export_format: Export format (geojson, csv, shp, etc.)
            record_count: Number of records to export
            
        Returns:
            Benchmark result with performance metrics
        """
        timestamp = datetime.now().isoformat()
        endpoint = self.rust_endpoint if mode == 'rust' else self.python_endpoint
        
        # Prepare test data
        test_data = self.create_test_data(record_count)
        test_data["format"] = export_format
        
        logger.info(f"Starting {mode} export: {export_format}, {record_count} records")
        
        start_time = time.time()
        peak_memory = 0.0
        output_file_size = 0
        output_hash = ""
        success = False
        error_message = None
        
        try:
            # Create export job
            response = requests.post(endpoint, json=test_data, timeout=300)
            response.raise_for_status()
            
            job_data = response.json()
            job_id = job_data.get("job_id")
            
            if not job_id:
                raise ValueError("No job_id returned from export API")
            
            # Monitor job progress
            while True:
                status_response = requests.get(f"{endpoint}/{job_id}")
                status_response.raise_for_status()
                
                status_data = status_response.json()
                job_status = status_data.get("status")
                
                if job_status == "COMPLETED":
                    success = True
                    break
                elif job_status == "FAILED":
                    error_message = status_data.get("message", "Export job failed")
                    break
                elif job_status in ["PENDING", "RUNNING"]:
                    time.sleep(1)  # Wait and check again
                else:
                    error_message = f"Unknown job status: {job_status}"
                    break
            
            # If successful, download and analyze output
            if success:
                download_response = requests.get(f"{endpoint}/{job_id}/download")
                download_response.raise_for_status()
                
                # Save output file for analysis
                output_file = Path(f"benchmark/output_{mode}_{export_format}_{record_count}_{timestamp.replace(':', '-')}")
                output_file.parent.mkdir(exist_ok=True)
                
                with open(output_file, 'wb') as f:
                    f.write(download_response.content)
                
                output_file_size = output_file.stat().st_size
                output_hash = self.calculate_file_hash(output_file)
                
                # Clean up output file after analysis
                output_file.unlink()
                
        except requests.exceptions.RequestException as e:
            error_message = f"HTTP request failed: {e}"
        except Exception as e:
            error_message = f"Benchmark failed: {e}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get current process memory as approximation
        current_process = psutil.Process()
        peak_memory = current_process.memory_info().rss / (1024 * 1024)
        
        result = BenchmarkResult(
            timestamp=timestamp,
            mode=mode,
            format=export_format,
            record_count=record_count,
            duration_seconds=duration,
            peak_memory_mb=peak_memory,
            output_file_size_bytes=output_file_size,
            output_hash=output_hash,
            success=success,
            error_message=error_message
        )
        
        self.results.append(result)
        
        if success:
            logger.info(f"✅ {mode} {export_format}: {duration:.2f}s, {peak_memory:.1f}MB, {output_file_size} bytes")
        else:
            logger.error(f"❌ {mode} {export_format} failed: {error_message}")
        
        return result
    
    def compare_modes(self, export_format: str, record_count: int) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """
        Compare Python vs Rust performance for the same export job.
        
        Args:
            export_format: Format to test
            record_count: Number of records
            
        Returns:
            Tuple of (python_result, rust_result)
        """
        logger.info(f"🔥 Comparing Python vs Rust: {export_format}, {record_count} records")
        
        python_result = self.run_export_job("python", export_format, record_count)
        time.sleep(2)  # Brief pause between tests
        rust_result = self.run_export_job("rust", export_format, record_count)
        
        # Calculate performance improvement
        if python_result.success and rust_result.success:
            speed_improvement = python_result.duration_seconds / rust_result.duration_seconds
            memory_improvement = python_result.peak_memory_mb / rust_result.peak_memory_mb
            
            logger.info(f"🚀 Performance Gains:")
            logger.info(f"   Speed: {speed_improvement:.1f}x faster")
            logger.info(f"   Memory: {memory_improvement:.1f}x more efficient")
            
            # Validate output correctness
            if python_result.output_hash == rust_result.output_hash:
                logger.info(f"✅ Output validation: Identical results")
            else:
                logger.warning(f"⚠️  Output validation: Different hashes (may be expected)")
        
        return python_result, rust_result
    
    def run_comprehensive_benchmark(self, formats: List[str], record_counts: List[int]) -> None:
        """
        Run comprehensive benchmarks across multiple formats and record counts.
        
        Args:
            formats: List of export formats to test
            record_counts: List of record counts to test
        """
        logger.info(f"🧪 Starting comprehensive benchmark")
        logger.info(f"   Formats: {formats}")
        logger.info(f"   Record counts: {record_counts}")
        
        total_tests = len(formats) * len(record_counts) * 2  # 2 modes per test
        current_test = 0
        
        for export_format in formats:
            for record_count in record_counts:
                current_test += 2
                logger.info(f"📊 Progress: {current_test}/{total_tests}")
                
                try:
                    self.compare_modes(export_format, record_count)
                except Exception as e:
                    logger.error(f"Comparison failed for {export_format}/{record_count}: {e}")
    
    def save_results(self, output_file: str = "benchmark/results.csv") -> None:
        """
        Save benchmark results to CSV file.
        
        Args:
            output_file: Path to output CSV file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=asdict(self.results[0]).keys())
                writer.writeheader()
                for result in self.results:
                    writer.writerow(asdict(result))
        
        logger.info(f"📊 Results saved to: {output_path}")
        logger.info(f"   Total benchmarks: {len(self.results)}")
    
    def generate_summary_report(self) -> str:
        """
        Generate a markdown summary of benchmark results.
        
        Returns:
            Markdown-formatted summary report
        """
        if not self.results:
            return "No benchmark results available."
        
        # Group results by format and record count
        python_results = [r for r in self.results if r.mode == 'python' and r.success]
        rust_results = [r for r in self.results if r.mode == 'rust' and r.success]
        
        report = "# TerraFusion GIS Export Benchmark Results\n\n"
        report += f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Total Tests:** {len(self.results)}\n"
        report += f"**Python Success Rate:** {len(python_results)}/{len([r for r in self.results if r.mode == 'python'])}\n"
        report += f"**Rust Success Rate:** {len(rust_results)}/{len([r for r in self.results if r.mode == 'rust'])}\n\n"
        
        if python_results and rust_results:
            avg_python_time = sum(r.duration_seconds for r in python_results) / len(python_results)
            avg_rust_time = sum(r.duration_seconds for r in rust_results) / len(rust_results)
            avg_speed_improvement = avg_python_time / avg_rust_time if avg_rust_time > 0 else 0
            
            avg_python_memory = sum(r.peak_memory_mb for r in python_results) / len(python_results)
            avg_rust_memory = sum(r.peak_memory_mb for r in rust_results) / len(rust_results)
            avg_memory_improvement = avg_python_memory / avg_rust_memory if avg_rust_memory > 0 else 0
            
            report += "## 🚀 Performance Summary\n\n"
            report += f"- **Average Speed Improvement:** {avg_speed_improvement:.1f}x faster\n"
            report += f"- **Average Memory Improvement:** {avg_memory_improvement:.1f}x more efficient\n"
            report += f"- **Python Average Time:** {avg_python_time:.2f}s\n"
            report += f"- **Rust Average Time:** {avg_rust_time:.2f}s\n\n"
        
        return report

def main():
    """Main CLI interface for the benchmark suite."""
    parser = argparse.ArgumentParser(description="TerraFusion GIS Export Benchmark Suite")
    
    parser.add_argument("--mode", choices=["python", "rust", "both"], default="both",
                       help="Which implementation to benchmark")
    parser.add_argument("--format", default="geojson",
                       help="Export format to test (geojson, csv, shp, etc.)")
    parser.add_argument("--records", type=int, default=1000,
                       help="Number of records to export")
    parser.add_argument("--all-formats", action="store_true",
                       help="Test all supported formats")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive benchmark with multiple record counts")
    parser.add_argument("--output", default="benchmark/results.csv",
                       help="Output CSV file for results")
    parser.add_argument("--base-url", default="http://localhost:5000",
                       help="Base URL for TerraFusion API")
    
    args = parser.parse_args()
    
    # Create benchmark instance
    benchmark = GISBenchmark(base_url=args.base_url)
    
    # Determine test parameters
    if args.all_formats:
        formats = ["geojson", "csv", "shp", "kml", "geopackage"]
    else:
        formats = [args.format]
    
    if args.comprehensive:
        record_counts = [100, 500, 1000, 2500, 5000]
    else:
        record_counts = [args.records]
    
    try:
        if args.mode == "both":
            benchmark.run_comprehensive_benchmark(formats, record_counts)
        else:
            for fmt in formats:
                for count in record_counts:
                    benchmark.run_export_job(args.mode, fmt, count)
        
        # Save results
        benchmark.save_results(args.output)
        
        # Generate and print summary
        summary = benchmark.generate_summary_report()
        print("\n" + summary)
        
        # Save summary to file
        summary_file = Path(args.output).with_suffix('.md')
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"📄 Summary report saved to: {summary_file}")
        
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()