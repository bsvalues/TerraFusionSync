#!/bin/bash
# TerraFusion Platform - Deployment Validation Script
# Comprehensive validation for county deployment readiness

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Output file
REPORT_FILE="terrafusion_validation_report.json"

echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}TerraFusion Platform - Deployment Validation${NC}"
echo -e "${CYAN}=================================================================${NC}"
echo ""

# Initialize JSON report
cat > "$REPORT_FILE" << EOF
{
  "testSuite": "TerraFusion County Deployment Validation",
  "testDate": "$(date -Iseconds)",
  "environment": {
    "os": "$(uname -s)",
    "architecture": "$(uname -m)",
    "kernelVersion": "$(uname -r)",
    "timestamp": "$(date)"
  },
  "tests": [
EOF

add_test_result() {
    local category="$1"
    local test_name="$2"
    local status="$3"
    local message="$4"
    local critical="${5:-true}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    case "$status" in
        "PASS")
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo -e "    ${GREEN}[✓]${NC} $category - $test_name"
            icon="✓"
            ;;
        "FAIL")
            FAILED_TESTS=$((FAILED_TESTS + 1))
            echo -e "    ${RED}[✗]${NC} $category - $test_name"
            icon="✗"
            ;;
        "WARN")
            WARNING_TESTS=$((WARNING_TESTS + 1))
            echo -e "    ${YELLOW}[⚠]${NC} $category - $test_name"
            icon="⚠"
            ;;
    esac
    
    if [ "$message" != "" ]; then
        echo -e "        ${message}"
    fi
    
    # Add to JSON report (append comma if not first test)
    if [ $TOTAL_TESTS -gt 1 ]; then
        echo "," >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF
    {
      "category": "$category",
      "testName": "$test_name",
      "status": "$status",
      "message": "$message",
      "critical": $critical,
      "timestamp": "$(date -Iseconds)"
    }EOF
}

test_api_gateway() {
    echo -e "${YELLOW}Testing API Gateway...${NC}"
    
    # Test API Gateway response
    if curl -s -f http://localhost:5000/api/status > /dev/null 2>&1; then
        add_test_result "Network" "API Gateway" "PASS" "API Gateway responding on port 5000"
        
        # Test API health
        response=$(curl -s http://localhost:5000/api/status 2>/dev/null || echo "")
        if echo "$response" | grep -q '"status":"success"'; then
            add_test_result "Network" "API Health" "PASS" "API health check successful"
        else
            add_test_result "Network" "API Health" "WARN" "API health check returned unexpected response" false
        fi
    else
        add_test_result "Network" "API Gateway" "FAIL" "API Gateway not accessible on port 5000"
    fi
}

test_sync_service() {
    echo -e "${YELLOW}Testing Sync Service...${NC}"
    
    # Test Sync Service
    if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
        add_test_result "Network" "Sync Service" "PASS" "Sync Service responding on port 8080"
    else
        add_test_result "Network" "Sync Service" "WARN" "Sync Service not accessible (may be internal only)" false
    fi
}

test_enhanced_endpoints() {
    echo -e "${YELLOW}Testing Enhanced Endpoints...${NC}"
    
    # Test enhanced API endpoints
    endpoints=("/api/help" "/api/formats" "/api/version")
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "http://localhost:5000$endpoint" > /dev/null 2>&1; then
            add_test_result "API" "Enhanced Endpoint $endpoint" "PASS" "Enhanced endpoint responding"
        else
            add_test_result "API" "Enhanced Endpoint $endpoint" "WARN" "Enhanced endpoint not available" false
        fi
    done
}

test_gis_capabilities() {
    echo -e "${YELLOW}Testing GIS Capabilities...${NC}"
    
    # Test GIS export formats
    if curl -s -f http://localhost:5000/api/formats > /dev/null 2>&1; then
        formats_response=$(curl -s http://localhost:5000/api/formats 2>/dev/null || echo "")
        if echo "$formats_response" | grep -q "supported_formats"; then
            format_count=$(echo "$formats_response" | grep -o '"[^"]*":' | wc -l)
            add_test_result "GIS" "Export Formats" "PASS" "$format_count export formats available"
        else
            add_test_result "GIS" "Export Formats" "FAIL" "GIS export formats not properly configured"
        fi
    else
        add_test_result "GIS" "Export Formats" "FAIL" "GIS export engine not responding"
    fi
    
    # Test district lookup
    if curl -s -f http://localhost:5000/api/v1/district-lookup/districts > /dev/null 2>&1; then
        add_test_result "GIS" "District Lookup" "PASS" "District lookup service available"
    else
        add_test_result "GIS" "District Lookup" "WARN" "District lookup service not responding" false
    fi
}

test_ai_features() {
    echo -e "${YELLOW}Testing AI Features...${NC}"
    
    # Test AI health endpoint
    if curl -s -f http://localhost:5000/api/v1/ai/health > /dev/null 2>&1; then
        ai_response=$(curl -s http://localhost:5000/api/v1/ai/health 2>/dev/null || echo "")
        if echo "$ai_response" | grep -q "status"; then
            add_test_result "AI" "NarratorAI Health" "PASS" "NarratorAI service responding"
        else
            add_test_result "AI" "NarratorAI Health" "WARN" "NarratorAI service returned unexpected response" false
        fi
    else
        add_test_result "AI" "NarratorAI Health" "WARN" "NarratorAI service not accessible" false
    fi
    
    # Test AI demo endpoint
    if curl -s -f http://localhost:5000/api/v1/ai/demo > /dev/null 2>&1; then
        add_test_result "AI" "AI Demo" "PASS" "AI demonstration endpoint working"
    else
        add_test_result "AI" "AI Demo" "WARN" "AI demonstration not available" false
    fi
}

test_monitoring_integration() {
    echo -e "${YELLOW}Testing Monitoring Integration...${NC}"
    
    # Test for monitoring files
    if [ -f "grafana/terrafusion_monitoring.json" ]; then
        add_test_result "Monitoring" "Grafana Dashboard" "PASS" "Grafana dashboard configuration available"
    else
        add_test_result "Monitoring" "Grafana Dashboard" "WARN" "Grafana dashboard not found" false
    fi
    
    if [ -f "prometheus_terrafusion.yml" ]; then
        add_test_result "Monitoring" "Prometheus Config" "PASS" "Prometheus configuration available"
    else
        add_test_result "Monitoring" "Prometheus Config" "WARN" "Prometheus configuration not found" false
    fi
}

test_benchmark_suite() {
    echo -e "${YELLOW}Testing Benchmark Suite...${NC}"
    
    if [ -f "benchmark/compare_gis.py" ]; then
        add_test_result "Performance" "Benchmark Suite" "PASS" "Performance benchmark tools available"
    else
        add_test_result "Performance" "Benchmark Suite" "WARN" "Benchmark suite not found" false
    fi
    
    if [ -f "benchmark/README.md" ]; then
        add_test_result "Performance" "Benchmark Documentation" "PASS" "Benchmark documentation available"
    else
        add_test_result "Performance" "Benchmark Documentation" "WARN" "Benchmark documentation missing" false
    fi
}

test_configuration_system() {
    echo -e "${YELLOW}Testing Configuration System...${NC}"
    
    if [ -f "config_validator.py" ]; then
        add_test_result "Configuration" "Config Validator" "PASS" "Configuration validation system available"
    else
        add_test_result "Configuration" "Config Validator" "WARN" "Configuration validator not found" false
    fi
    
    if [ -f "enhanced_api_endpoints.py" ]; then
        add_test_result "Configuration" "Enhanced Endpoints" "PASS" "Enhanced API endpoints available"
    else
        add_test_result "Configuration" "Enhanced Endpoints" "WARN" "Enhanced endpoints not found" false
    fi
}

test_documentation() {
    echo -e "${YELLOW}Testing Documentation...${NC}"
    
    docs=("README_IT.md" "README_GRAFANA.md" "installer/README_INSTALL.md")
    
    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            add_test_result "Documentation" "$(basename "$doc")" "PASS" "Documentation file available"
        else
            add_test_result "Documentation" "$(basename "$doc")" "WARN" "Documentation file missing" false
        fi
    done
}

test_installer_package() {
    echo -e "${YELLOW}Testing Installer Package...${NC}"
    
    installer_files=("installer/installer.nsi" "installer/scripts/install_ollama.bat" "installer/scripts/register_services.bat" "installer/verify_install.ps1")
    
    for file in "${installer_files[@]}"; do
        if [ -f "$file" ]; then
            add_test_result "Installer" "$(basename "$file")" "PASS" "Installer component available"
        else
            add_test_result "Installer" "$(basename "$file")" "FAIL" "Critical installer component missing"
        fi
    done
}

# Run all tests
echo "Starting comprehensive deployment validation..."
echo ""

test_api_gateway
test_sync_service
test_enhanced_endpoints
test_gis_capabilities
test_ai_features
test_monitoring_integration
test_benchmark_suite
test_configuration_system
test_documentation
test_installer_package

# Close JSON report
cat >> "$REPORT_FILE" << EOF
  ],
  "summary": {
    "totalTests": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "warnings": $WARNING_TESTS,
    "overallStatus": "$(if [ $FAILED_TESTS -eq 0 ]; then echo "PASS"; elif [ $FAILED_TESTS -le 2 ]; then echo "PARTIAL"; else echo "FAIL"; fi)"
  }
}
EOF

# Display summary
echo ""
echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}Validation Summary${NC}"
echo -e "${CYAN}=================================================================${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 DEPLOYMENT VALIDATION SUCCESSFUL${NC}"
    echo ""
    echo -e "${GREEN}Your TerraFusion Platform is ready for county deployment!${NC}"
    echo -e "${CYAN}Access the platform at: http://localhost:5000${NC}"
    
    if [ $WARNING_TESTS -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Note: $WARNING_TESTS optional features have warnings.${NC}"
        echo -e "${YELLOW}The platform will work, but some features may be limited.${NC}"
    fi
else
    echo -e "${RED}⚠️ DEPLOYMENT ISSUES DETECTED${NC}"
    echo ""
    echo -e "${RED}Critical issues found that may affect operation.${NC}"
    echo -e "${RED}Please review the failed tests and resolve issues.${NC}"
fi

echo ""
echo -e "Test Results:"
echo -e "  Total Tests: $TOTAL_TESTS"
echo -e "  ${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
echo -e "  ${YELLOW}Warnings: $WARNING_TESTS${NC}"

echo ""
echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}Next Steps${NC}"
echo -e "${CYAN}=================================================================${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "1. ${GREEN}✓${NC} Platform validation complete - ready for deployment"
    echo -e "2. ${GREEN}✓${NC} All critical components operational"
    echo -e "3. ${CYAN}→${NC} Package for county distribution"
    echo -e "4. ${CYAN}→${NC} Coordinate pilot deployments"
    echo -e "5. ${CYAN}→${NC} Train county IT staff"
else
    echo -e "1. ${RED}✗${NC} Review failed tests and resolve issues"
    echo -e "2. ${YELLOW}⚠${NC} Check service logs for additional details"
    echo -e "3. ${YELLOW}⚠${NC} Verify all dependencies are properly installed"
    echo -e "4. ${CYAN}→${NC} Re-run validation after fixes"
fi

echo ""
echo -e "${CYAN}Detailed validation report saved to: $REPORT_FILE${NC}"
echo ""

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}TerraFusion Platform: COUNTY DEPLOYMENT READY! 🎉${NC}"
    exit 0
else
    echo -e "${RED}TerraFusion Platform: Issues require attention before deployment${NC}"
    exit 1
fi