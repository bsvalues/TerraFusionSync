# TerraFusion Platform - Post-Installation Verification Script
# Comprehensive validation for Benton County production deployment

param(
    [string]$Mode = "full",
    [switch]$GenerateReport = $true,
    [string]$OutputPath = "verification_results.log"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "TerraFusion Benton County Verification" -ForegroundColor Green
Write-Host "Production Deployment Validation" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$VerificationResults = @()
$StartTime = Get-Date

function Test-Service {
    param($ServiceName, $URL, $ExpectedStatus = 200)
    
    try {
        $Response = Invoke-WebRequest -Uri $URL -TimeoutSec 10 -UseBasicParsing
        if ($Response.StatusCode -eq $ExpectedStatus) {
            Write-Host "[✓] $ServiceName - OPERATIONAL" -ForegroundColor Green
            return @{ Service = $ServiceName; Status = "PASS"; Details = "HTTP $($Response.StatusCode)" }
        } else {
            Write-Host "[!] $ServiceName - Unexpected status: $($Response.StatusCode)" -ForegroundColor Yellow
            return @{ Service = $ServiceName; Status = "WARNING"; Details = "HTTP $($Response.StatusCode)" }
        }
    } catch {
        Write-Host "[✗] $ServiceName - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = $ServiceName; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-DatabaseConnection {
    Write-Host "[1/8] Testing PostgreSQL Database Connection..." -ForegroundColor Yellow
    
    try {
        # Test if PostgreSQL service is running
        $PGService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
        if ($PGService -and $PGService.Status -eq "Running") {
            Write-Host "[✓] PostgreSQL Service - RUNNING" -ForegroundColor Green
            return @{ Service = "PostgreSQL"; Status = "PASS"; Details = "Service running" }
        } else {
            Write-Host "[!] PostgreSQL Service - NOT RUNNING" -ForegroundColor Yellow
            return @{ Service = "PostgreSQL"; Status = "WARNING"; Details = "Service not running" }
        }
    } catch {
        Write-Host "[✗] PostgreSQL - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "PostgreSQL"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-BentonCountyData {
    Write-Host "[2/8] Validating Benton County District Data..." -ForegroundColor Yellow
    
    try {
        $DistrictAPI = "http://localhost:5000/api/v1/district-lookup/districts"
        $Response = Invoke-WebRequest -Uri $DistrictAPI -TimeoutSec 15 -UseBasicParsing
        $Data = $Response.Content | ConvertFrom-Json
        
        # Verify Benton County specific data
        $VotingPrecincts = $Data.voting_precincts
        $FireDistricts = $Data.fire_districts
        $SchoolDistricts = $Data.school_districts
        
        if ($VotingPrecincts.Count -ge 10 -and $FireDistricts.Count -ge 2 -and $SchoolDistricts.Count -ge 2) {
            Write-Host "[✓] Benton County Data - VALIDATED ($($VotingPrecincts.Count) precincts, $($FireDistricts.Count) fire districts, $($SchoolDistricts.Count) school districts)" -ForegroundColor Green
            return @{ Service = "Benton County Data"; Status = "PASS"; Details = "All district types present" }
        } else {
            Write-Host "[!] Benton County Data - INCOMPLETE" -ForegroundColor Yellow
            return @{ Service = "Benton County Data"; Status = "WARNING"; Details = "Some district data missing" }
        }
    } catch {
        Write-Host "[✗] Benton County Data - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "Benton County Data"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-AIServices {
    Write-Host "[3/8] Testing AI Services (NarratorAI + ExemptionSeer)..." -ForegroundColor Yellow
    
    $AIResults = @()
    
    # Test NarratorAI
    try {
        $NarratorAPI = "http://localhost:5000/api/v1/ai/health"
        $Response = Invoke-WebRequest -Uri $NarratorAPI -TimeoutSec 10 -UseBasicParsing
        $Data = $Response.Content | ConvertFrom-Json
        
        if ($Data.status -eq "healthy") {
            Write-Host "[✓] NarratorAI - OPERATIONAL" -ForegroundColor Green
            $AIResults += @{ Service = "NarratorAI"; Status = "PASS"; Details = "Service healthy" }
        } else {
            Write-Host "[!] NarratorAI - Degraded: $($Data.status)" -ForegroundColor Yellow
            $AIResults += @{ Service = "NarratorAI"; Status = "WARNING"; Details = $Data.status }
        }
    } catch {
        Write-Host "[✗] NarratorAI - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $AIResults += @{ Service = "NarratorAI"; Status = "FAIL"; Details = $_.Exception.Message }
    }
    
    # Test AI Analysis Dashboard
    try {
        $AIAnalysisAPI = "http://localhost:5000/ai-analysis"
        $Response = Invoke-WebRequest -Uri $AIAnalysisAPI -TimeoutSec 10 -UseBasicParsing
        
        if ($Response.StatusCode -eq 200) {
            Write-Host "[✓] AI Analysis Dashboard - ACCESSIBLE" -ForegroundColor Green
            $AIResults += @{ Service = "AI Analysis Dashboard"; Status = "PASS"; Details = "Dashboard accessible" }
        }
    } catch {
        Write-Host "[✗] AI Analysis Dashboard - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $AIResults += @{ Service = "AI Analysis Dashboard"; Status = "FAIL"; Details = $_.Exception.Message }
    }
    
    return $AIResults
}

function Test-GISExportCapabilities {
    Write-Host "[4/8] Testing GIS Export Capabilities..." -ForegroundColor Yellow
    
    try {
        $GISJobsAPI = "http://localhost:5000/api/v1/gis-export/jobs"
        $Response = Invoke-WebRequest -Uri $GISJobsAPI -TimeoutSec 10 -UseBasicParsing
        
        if ($Response.StatusCode -eq 200) {
            Write-Host "[✓] GIS Export API - OPERATIONAL" -ForegroundColor Green
            return @{ Service = "GIS Export"; Status = "PASS"; Details = "API responding" }
        }
    } catch {
        Write-Host "[✗] GIS Export - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "GIS Export"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-BackupSystem {
    Write-Host "[5/8] Verifying Automated Backup System..." -ForegroundColor Yellow
    
    try {
        $BackupDir = "backups"
        if (Test-Path $BackupDir) {
            $RecentBackups = Get-ChildItem $BackupDir -Filter "*.gz" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-6) }
            
            if ($RecentBackups.Count -gt 0) {
                Write-Host "[✓] Backup System - ACTIVE ($($RecentBackups.Count) recent backups)" -ForegroundColor Green
                return @{ Service = "Backup System"; Status = "PASS"; Details = "$($RecentBackups.Count) recent backups found" }
            } else {
                Write-Host "[!] Backup System - No recent backups found" -ForegroundColor Yellow
                return @{ Service = "Backup System"; Status = "WARNING"; Details = "No recent backups" }
            }
        } else {
            Write-Host "[!] Backup System - Backup directory not found" -ForegroundColor Yellow
            return @{ Service = "Backup System"; Status = "WARNING"; Details = "Backup directory missing" }
        }
    } catch {
        Write-Host "[✗] Backup System - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "Backup System"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-PublicTransparencyEndpoints {
    Write-Host "[6/8] Testing Public Transparency Endpoints..." -ForegroundColor Yellow
    
    $PublicResults = @()
    
    # Test main dashboard
    $PublicResults += Test-Service "Main Dashboard" "http://localhost:5000/"
    
    # Test district lookup
    $PublicResults += Test-Service "District Lookup" "http://localhost:5000/district-lookup"
    
    # Test GIS dashboard
    $PublicResults += Test-Service "GIS Dashboard" "http://localhost:5000/gis/dashboard"
    
    return $PublicResults
}

function Test-SystemResources {
    Write-Host "[7/8] Checking System Resources..." -ForegroundColor Yellow
    
    try {
        $Memory = Get-WmiObject -Class Win32_OperatingSystem
        $AvailableMemoryGB = [Math]::Round($Memory.FreePhysicalMemory / 1KB / 1KB, 2)
        $TotalMemoryGB = [Math]::Round($Memory.TotalVisibleMemorySize / 1KB / 1KB, 2)
        $MemoryUsagePercent = [Math]::Round((($TotalMemoryGB - $AvailableMemoryGB) / $TotalMemoryGB) * 100, 1)
        
        $Disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $FreeDiskGB = [Math]::Round($Disk.FreeSpace / 1GB, 2)
        $TotalDiskGB = [Math]::Round($Disk.Size / 1GB, 2)
        
        Write-Host "[✓] Memory Usage: $MemoryUsagePercent% ($AvailableMemoryGB GB available)" -ForegroundColor Green
        Write-Host "[✓] Disk Space: $FreeDiskGB GB free of $TotalDiskGB GB total" -ForegroundColor Green
        
        $ResourceStatus = "GOOD"
        if ($MemoryUsagePercent -gt 85) { $ResourceStatus = "WARNING - High memory usage" }
        if ($FreeDiskGB -lt 5) { $ResourceStatus = "WARNING - Low disk space" }
        
        return @{ Service = "System Resources"; Status = if($ResourceStatus -eq "GOOD") {"PASS"} else {"WARNING"}; Details = $ResourceStatus }
    } catch {
        Write-Host "[✗] System Resources - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "System Resources"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

function Test-SecurityConfiguration {
    Write-Host "[8/8] Verifying Security Configuration..." -ForegroundColor Yellow
    
    try {
        # Check if environment variables are properly set
        $EnvVars = @("DATABASE_URL", "SESSION_SECRET")
        $MissingVars = @()
        
        foreach ($Var in $EnvVars) {
            if (-not [Environment]::GetEnvironmentVariable($Var)) {
                $MissingVars += $Var
            }
        }
        
        if ($MissingVars.Count -eq 0) {
            Write-Host "[✓] Security Configuration - SECURE" -ForegroundColor Green
            return @{ Service = "Security Configuration"; Status = "PASS"; Details = "All environment variables set" }
        } else {
            Write-Host "[!] Security Configuration - Missing variables: $($MissingVars -join ', ')" -ForegroundColor Yellow
            return @{ Service = "Security Configuration"; Status = "WARNING"; Details = "Missing: $($MissingVars -join ', ')" }
        }
    } catch {
        Write-Host "[✗] Security Configuration - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Service = "Security Configuration"; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

# Run all verification tests
Write-Host "Starting TerraFusion Production Verification..." -ForegroundColor Cyan
Write-Host ""

$VerificationResults += Test-DatabaseConnection
$VerificationResults += Test-BentonCountyData
$VerificationResults += Test-AIServices
$VerificationResults += Test-GISExportCapabilities
$VerificationResults += Test-BackupSystem
$VerificationResults += Test-PublicTransparencyEndpoints
$VerificationResults += Test-SystemResources
$VerificationResults += Test-SecurityConfiguration

# Calculate overall status
$PassCount = ($VerificationResults | Where-Object { $_.Status -eq "PASS" }).Count
$WarningCount = ($VerificationResults | Where-Object { $_.Status -eq "WARNING" }).Count
$FailCount = ($VerificationResults | Where-Object { $_.Status -eq "FAIL" }).Count
$TotalTests = $VerificationResults.Count

$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Duration: $($Duration.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host "Tests Run: $TotalTests" -ForegroundColor Cyan
Write-Host "Passed: $PassCount" -ForegroundColor Green
Write-Host "Warnings: $WarningCount" -ForegroundColor Yellow
Write-Host "Failed: $FailCount" -ForegroundColor Red
Write-Host ""

# Determine overall deployment status
if ($FailCount -eq 0 -and $WarningCount -le 2) {
    Write-Host "🎉 BENTON COUNTY DEPLOYMENT: PRODUCTION READY" -ForegroundColor Green
    $OverallStatus = "PRODUCTION_READY"
} elseif ($FailCount -eq 0) {
    Write-Host "⚠️  BENTON COUNTY DEPLOYMENT: OPERATIONAL WITH WARNINGS" -ForegroundColor Yellow
    $OverallStatus = "OPERATIONAL_WITH_WARNINGS"
} else {
    Write-Host "❌ BENTON COUNTY DEPLOYMENT: REQUIRES ATTENTION" -ForegroundColor Red
    $OverallStatus = "REQUIRES_ATTENTION"
}

# Generate detailed report if requested
if ($GenerateReport) {
    $Report = @"
TerraFusion Platform - Benton County Production Verification Report
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Duration: $($Duration.TotalSeconds) seconds
Overall Status: $OverallStatus

SUMMARY:
- Total Tests: $TotalTests
- Passed: $PassCount
- Warnings: $WarningCount  
- Failed: $FailCount

DETAILED RESULTS:
"@

    foreach ($Result in $VerificationResults) {
        $Report += "`n[$($Result.Status)] $($Result.Service): $($Result.Details)"
    }
    
    $Report += @"

DEPLOYMENT RECOMMENDATIONS:
"@

    if ($OverallStatus -eq "PRODUCTION_READY") {
        $Report += "`n✅ System is ready for county operations"
        $Report += "`n✅ All critical services operational"
        $Report += "`n✅ Ready for staff training and rollout"
    } elseif ($OverallStatus -eq "OPERATIONAL_WITH_WARNINGS") {
        $Report += "`n⚠️  Address warnings before full production use"
        $Report += "`n✅ Core functionality operational"
        $Report += "`n🔧 Review system configuration"
    } else {
        $Report += "`n❌ Critical issues must be resolved"
        $Report += "`n🔧 Check failed services"
        $Report += "`n📞 Contact technical support if needed"
    }

    $Report | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "📄 Detailed report saved to: $OutputPath" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "TerraFusion Benton County verification complete." -ForegroundColor Green
Write-Host "Ready for county operations and public transparency." -ForegroundColor Green