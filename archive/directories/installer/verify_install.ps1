# TerraFusion Platform - Installation Verification Script
# PowerShell script to validate a successful TerraFusion installation

param(
    [switch]$Detailed,
    [switch]$ExportLogs,
    [string]$OutputPath = "C:\ProgramData\TerraFusion\validation_report.txt"
)

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "TerraFusion Platform - Installation Verification" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0
$ValidationResults = @()

function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$SuccessMessage,
        [string]$ErrorMessage,
        [bool]$Critical = $true
    )
    
    Write-Host "Testing $Name..." -NoNewline
    
    try {
        $Result = & $Test
        if ($Result) {
            Write-Host " [OK]" -ForegroundColor Green
            $ValidationResults += @{
                Component = $Name
                Status = "PASS"
                Message = $SuccessMessage
                Critical = $Critical
            }
            return $true
        } else {
            if ($Critical) {
                Write-Host " [FAIL]" -ForegroundColor Red
                $script:ErrorCount++
            } else {
                Write-Host " [WARN]" -ForegroundColor Yellow
                $script:WarningCount++
            }
            $ValidationResults += @{
                Component = $Name
                Status = if ($Critical) { "FAIL" } else { "WARN" }
                Message = $ErrorMessage
                Critical = $Critical
            }
            return $false
        }
    } catch {
        if ($Critical) {
            Write-Host " [ERROR]" -ForegroundColor Red
            $script:ErrorCount++
        } else {
            Write-Host " [WARN]" -ForegroundColor Yellow
            $script:WarningCount++
        }
        $ValidationResults += @{
            Component = $Name
            Status = if ($Critical) { "ERROR" } else { "WARN" }
            Message = "$ErrorMessage - Exception: $($_.Exception.Message)"
            Critical = $Critical
        }
        return $false
    }
}

# Test 1: Installation Directory
Test-Component -Name "Installation Directory" -Test {
    Test-Path "C:\Program Files\TerraFusion"
} -SuccessMessage "TerraFusion installed in correct location" -ErrorMessage "Installation directory not found"

# Test 2: Core Executables
Test-Component -Name "Core Executables" -Test {
    (Test-Path "C:\Program Files\TerraFusion\bin\terrafusion_gateway.exe") -and
    (Test-Path "C:\Program Files\TerraFusion\bin\sync_service.exe")
} -SuccessMessage "Core platform executables found" -ErrorMessage "Missing core platform files"

# Test 3: Configuration Files
Test-Component -Name "Configuration Files" -Test {
    Test-Path "C:\Program Files\TerraFusion\config\county.env"
} -SuccessMessage "County configuration file created" -ErrorMessage "Configuration file missing" -Critical $false

# Test 4: Windows Services
Test-Component -Name "TerraFusion Gateway Service" -Test {
    $Service = Get-Service -Name "TerraFusion Gateway" -ErrorAction SilentlyContinue
    $Service -and ($Service.Status -eq "Running")
} -SuccessMessage "Gateway service running" -ErrorMessage "Gateway service not running or not installed"

Test-Component -Name "TerraFusion Sync Service" -Test {
    $Service = Get-Service -Name "TerraFusion Sync" -ErrorAction SilentlyContinue
    $Service -and ($Service.Status -eq "Running")
} -SuccessMessage "Sync service running" -ErrorMessage "Sync service not running or not installed"

# Test 5: Network Connectivity
Test-Component -Name "API Gateway Response" -Test {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $Response.StatusCode -eq 200
    } catch {
        $false
    }
} -SuccessMessage "API Gateway responding on port 5000" -ErrorMessage "API Gateway not accessible"

# Test 6: Database Connection
Test-Component -Name "Database Connection" -Test {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $StatusData = $Response.Content | ConvertFrom-Json
        $StatusData.data.services.database -eq "healthy"
    } catch {
        $false
    }
} -SuccessMessage "Database connection established" -ErrorMessage "Database not accessible" -Critical $false

# Test 7: AI Features (Optional)
Test-Component -Name "Ollama AI Runtime" -Test {
    try {
        $OllamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
        $OllamaProcess -ne $null
    } catch {
        $false
    }
} -SuccessMessage "AI runtime available" -ErrorMessage "AI features not available" -Critical $false

# Test 8: GIS Export Capabilities
Test-Component -Name "GIS Export Formats" -Test {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/formats" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $FormatsData = $Response.Content | ConvertFrom-Json
        $FormatsData.data.supported_formats.Count -gt 0
    } catch {
        $false
    }
} -SuccessMessage "GIS export formats available" -ErrorMessage "GIS export engine not responding" -Critical $false

# Test 9: Log Directories
Test-Component -Name "Log Directories" -Test {
    (Test-Path "C:\Program Files\TerraFusion\logs") -and
    (Test-Path "C:\ProgramData\TerraFusion")
} -SuccessMessage "Log directories created" -ErrorMessage "Log directories missing" -Critical $false

# Test 10: Desktop Integration
Test-Component -Name "Desktop Shortcuts" -Test {
    Test-Path "$env:PUBLIC\Desktop\TerraFusion Platform.lnk"
} -SuccessMessage "Desktop shortcuts installed" -ErrorMessage "Desktop integration incomplete" -Critical $false

# Test 11: Start Menu Integration
Test-Component -Name "Start Menu Integration" -Test {
    Test-Path "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\TerraFusion Platform"
} -SuccessMessage "Start Menu folder created" -ErrorMessage "Start Menu integration missing" -Critical $false

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$TotalTests = $ValidationResults.Count
$PassedTests = ($ValidationResults | Where-Object { $_.Status -eq "PASS" }).Count
$FailedTests = ($ValidationResults | Where-Object { $_.Status -eq "FAIL" }).Count
$WarningTests = ($ValidationResults | Where-Object { $_.Status -eq "WARN" }).Count
$ErrorTests = ($ValidationResults | Where-Object { $_.Status -eq "ERROR" }).Count

Write-Host ""
Write-Host "Total Tests: $TotalTests" -ForegroundColor White
Write-Host "Passed: $PassedTests" -ForegroundColor Green
Write-Host "Failed: $FailedTests" -ForegroundColor Red
Write-Host "Warnings: $WarningTests" -ForegroundColor Yellow
Write-Host "Errors: $ErrorTests" -ForegroundColor Red
Write-Host ""

# Overall Assessment
if ($ErrorCount -eq 0) {
    Write-Host "OVERALL STATUS: INSTALLATION SUCCESSFUL" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your TerraFusion Platform is ready for use!" -ForegroundColor Green
    Write-Host "Access the platform at: http://localhost:5000" -ForegroundColor Cyan
    
    if ($WarningCount -gt 0) {
        Write-Host ""
        Write-Host "Note: $WarningCount optional features have warnings." -ForegroundColor Yellow
        Write-Host "The platform will work, but some features may be limited." -ForegroundColor Yellow
    }
} else {
    Write-Host "OVERALL STATUS: INSTALLATION ISSUES DETECTED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Critical issues found that prevent proper operation." -ForegroundColor Red
    Write-Host "Please review the failed tests and contact support." -ForegroundColor Red
}

# Detailed Results
if ($Detailed) {
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "Detailed Test Results" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    
    foreach ($Result in $ValidationResults) {
        $StatusColor = switch ($Result.Status) {
            "PASS" { "Green" }
            "WARN" { "Yellow" }
            "FAIL" { "Red" }
            "ERROR" { "Red" }
        }
        
        Write-Host ""
        Write-Host "$($Result.Component): $($Result.Status)" -ForegroundColor $StatusColor
        Write-Host "  $($Result.Message)" -ForegroundColor Gray
    }
}

# Export Logs
if ($ExportLogs) {
    Write-Host ""
    Write-Host "Exporting validation report to: $OutputPath" -ForegroundColor Cyan
    
    $ReportContent = @"
TerraFusion Platform Validation Report
Generated: $(Get-Date)
========================================

SUMMARY:
Total Tests: $TotalTests
Passed: $PassedTests
Failed: $FailedTests
Warnings: $WarningTests
Errors: $ErrorTests

OVERALL STATUS: $(if ($ErrorCount -eq 0) { "SUCCESS" } else { "FAILED" })

DETAILED RESULTS:

"@
    
    foreach ($Result in $ValidationResults) {
        $ReportContent += "`n$($Result.Component): $($Result.Status)`n"
        $ReportContent += "  $($Result.Message)`n"
    }
    
    $ReportContent += @"

RECOMMENDATIONS:
$(if ($ErrorCount -eq 0) {
    "- TerraFusion is ready for production use
- Access the platform at http://localhost:5000
- Review any warnings to ensure full functionality"
} else {
    "- Contact technical support for assistance
- Review failed tests and error messages
- Check Windows Event Viewer for additional details"
})

NEXT STEPS:
1. Verify all critical components are working
2. Test basic functionality (GIS export, district lookup)
3. Train county staff on platform usage
4. Set up regular backup procedures

For support, contact your system administrator or county IT department.
"@
    
    try {
        $ReportDir = Split-Path $OutputPath -Parent
        if (!(Test-Path $ReportDir)) {
            New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
        }
        
        $ReportContent | Out-File -FilePath $OutputPath -Encoding UTF8
        Write-Host "Report saved successfully." -ForegroundColor Green
    } catch {
        Write-Host "Failed to save report: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "1. Open web browser and navigate to http://localhost:5000" -ForegroundColor White
    Write-Host "2. Explore the TerraFusion dashboard and features" -ForegroundColor White
    Write-Host "3. Try creating a test GIS export job" -ForegroundColor White
    Write-Host "4. Test the district lookup functionality" -ForegroundColor White
    Write-Host "5. Review the user documentation and training materials" -ForegroundColor White
} else {
    Write-Host "1. Review the failed test results above" -ForegroundColor White
    Write-Host "2. Check Windows Event Viewer for additional error details" -ForegroundColor White
    Write-Host "3. Verify all services are properly installed and running" -ForegroundColor White
    Write-Host "4. Contact technical support with this validation report" -ForegroundColor White
    Write-Host "5. Consider reinstalling if critical issues persist" -ForegroundColor White
}

Write-Host ""
Write-Host "For additional help:" -ForegroundColor Cyan
Write-Host "- User Guide: Start Menu > TerraFusion Platform > User Guide" -ForegroundColor White
Write-Host "- Configuration: Start Menu > TerraFusion Platform > Configuration" -ForegroundColor White
Write-Host "- Online Help: http://localhost:5000/api/help" -ForegroundColor White

exit $(if ($ErrorCount -eq 0) { 0 } else { 1 })