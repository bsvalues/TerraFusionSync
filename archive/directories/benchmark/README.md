# 🧪 TerraFusion GIS Export Benchmark Suite

This benchmark suite measures and compares performance between Python and Rust GIS export implementations, providing quantifiable metrics on speed, memory usage, and output validation.

## 🎯 What It Measures

- **⚡ Processing Speed**: Job start to completion time
- **💾 Memory Usage**: Peak memory consumption during export
- **📊 Output Validation**: Hash comparison to ensure identical results
- **📈 Scalability**: Performance across different record counts
- **🔧 Format Support**: Testing across multiple export formats

## 🚀 Quick Start

### Basic Performance Test
```bash
# Compare Python vs Rust for 1000 records in GeoJSON format
python benchmark/compare_gis.py --format geojson --records 1000

# Test only Rust implementation with CSV format
python benchmark/compare_gis.py --mode rust --format csv --records 2500
```

### Comprehensive Benchmarking
```bash
# Test all formats with multiple record counts
python benchmark/compare_gis.py --comprehensive --all-formats

# Custom benchmark with specific parameters
python benchmark/compare_gis.py --comprehensive --format geojson --output my_results.csv
```

## 📊 Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Test mode: `python`, `rust`, or `both` | `both` |
| `--format` | Export format to test | `geojson` |
| `--records` | Number of records to export | `1000` |
| `--all-formats` | Test all supported formats | `false` |
| `--comprehensive` | Multiple record counts (100, 500, 1K, 2.5K, 5K) | `false` |
| `--output` | Results CSV file path | `benchmark/results.csv` |
| `--base-url` | TerraFusion API base URL | `http://localhost:5000` |

## 📈 Example Results

After running benchmarks, you'll see real-time performance comparisons:

```
2024-05-27 19:45:10 - INFO - 🔥 Comparing Python vs Rust: geojson, 1000 records
2024-05-27 19:45:12 - INFO - ✅ python geojson: 3.45s, 128.4MB, 245760 bytes
2024-05-27 19:45:14 - INFO - ✅ rust geojson: 0.89s, 45.2MB, 245760 bytes
2024-05-27 19:45:14 - INFO - 🚀 Performance Gains:
2024-05-27 19:45:14 - INFO -    Speed: 3.9x faster
2024-05-27 19:45:14 - INFO -    Memory: 2.8x more efficient
2024-05-27 19:45:14 - INFO - ✅ Output validation: Identical results
```

## 📋 Output Files

The benchmark generates several output files:

### `results.csv`
Complete benchmark data with columns:
- `timestamp`, `mode`, `format`, `record_count`
- `duration_seconds`, `peak_memory_mb`, `output_file_size_bytes`
- `output_hash`, `success`, `error_message`

### `results.md`
Markdown summary report with:
- Average performance improvements
- Success rates by implementation
- Test configuration details

## 🎛️ Supported Export Formats

| Format | Description | File Extension |
|--------|-------------|----------------|
| `geojson` | Geographic JSON | `.geojson` |
| `csv` | Comma-separated values | `.csv` |
| `shp` | ESRI Shapefile | `.shp` |
| `kml` | Keyhole Markup Language | `.kml` |
| `geopackage` | OGC GeoPackage | `.gpkg` |

## 🔧 Prerequisites

### Running Services
Ensure these TerraFusion services are running:
- **API Gateway**: `http://localhost:5000`
- **Sync Service**: `http://localhost:8080`
- **Database**: PostgreSQL with sample data

### Python Dependencies
The benchmark requires these packages (auto-installed):
```bash
pip install requests psutil
```

## 📊 Reading Results

### Performance Metrics
- **Speed Improvement**: `python_time / rust_time` ratio
- **Memory Efficiency**: `python_memory / rust_memory` ratio
- **Output Validation**: SHA256 hash comparison

### Interpreting Success Rates
- **100% Success**: Both implementations work perfectly
- **Mixed Success**: One implementation may have issues
- **Low Success**: Check API endpoints and data availability

## 🎯 Benchmark Scenarios

### Scenario 1: Quick Validation
```bash
python benchmark/compare_gis.py --records 100
```
Perfect for: Initial testing, CI/CD validation

### Scenario 2: Production Load Test
```bash
python benchmark/compare_gis.py --comprehensive --records 5000
```
Perfect for: Capacity planning, performance optimization

### Scenario 3: Format Compatibility
```bash
python benchmark/compare_gis.py --all-formats --records 1000
```
Perfect for: Ensuring consistent performance across formats

## 🔍 Troubleshooting

### Common Issues

**"Connection refused" errors:**
- Verify TerraFusion services are running
- Check API endpoints: `/api/v1/gis-export/jobs` and `/api/v2/gis-export/jobs`
- Confirm firewall settings

**"No job_id returned" errors:**
- Check API request format matches expected schema
- Verify county data is available in the database
- Review API logs for detailed error messages

**Memory monitoring inaccurate:**
- Memory measurements are approximate during active processing
- Results represent peak usage during the benchmark period
- Consider running isolated tests for precise measurements

### Debugging Mode
Add verbose logging:
```bash
python benchmark/compare_gis.py --format geojson --records 100 --verbose
```

## 📈 Integration with Grafana

Benchmark results can feed into your Grafana monitoring:

1. **Historical Trending**: Track performance over time
2. **Regression Detection**: Alert on performance degradation
3. **Capacity Planning**: Visualize scaling characteristics

### Importing to Grafana
```bash
# Convert benchmark results to Prometheus metrics format
python benchmark/export_to_prometheus.py results.csv
```

## 🎉 Expected Performance Gains

Based on Rust's advantages in systems programming:

| Metric | Expected Improvement |
|--------|---------------------|
| **Processing Speed** | 2-5x faster |
| **Memory Usage** | 2-3x more efficient |
| **CPU Utilization** | 30-50% reduction |
| **Concurrent Jobs** | 3-4x higher throughput |

## 🚀 Next Steps

After benchmarking:

1. **📊 Review Results**: Analyze performance patterns by format and scale
2. **📈 Update Grafana**: Import metrics for ongoing monitoring  
3. **🔧 Optimize**: Focus improvements on bottlenecks identified
4. **📱 Document**: Share results with stakeholders and county IT staff

---

Your TerraFusion platform now has quantifiable proof of its performance advantages! 🎯