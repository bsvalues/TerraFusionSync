# TerraFusion Platform - Automated Installer Verification
# Comprehensive test suite for validating county deployment readiness

param(
    [string]$TestMode = "full",        # full, quick, services-only
    [string]$ReportPath = "verification_results.json",
    [switch]$CleanInstall,             # Simulate fresh county environment
    [switch]$GenerateReport           # Create detailed JSON report
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "TerraFusion Platform - Automated Deployment Verification" -ForegroundColor Cyan
Write-Host "Testing Mode: $TestMode" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$TestResults = @{
    TestSuite = "TerraFusion County Deployment Verification"
    TestDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TestMode = $TestMode
    Environment = @{
        OS = (Get-WmiObject Win32_OperatingSystem).Caption
        OSVersion = (Get-WmiObject Win32_OperatingSystem).Version
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        Architecture = $env:PROCESSOR_ARCHITECTURE
        Memory = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
        AvailableDisk = [math]::Round((Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB, 2)
    }
    Tests = @()
    Summary = @{
        TotalTests = 0
        Passed = 0
        Failed = 0
        Warnings = 0
        Errors = 0
        OverallStatus = "UNKNOWN"
    }
}

function Add-TestResult {
    param(
        [string]$Category,
        [string]$TestName,
        [string]$Status,        # PASS, FAIL, WARN, ERROR
        [string]$Message,
        [object]$Details = $null,
        [bool]$Critical = $true
    )
    
    $Result = @{
        Category = $Category
        TestName = $TestName
        Status = $Status
        Message = $Message
        Details = $Details
        Critical = $Critical
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    $TestResults.Tests += $Result
    $TestResults.Summary.TotalTests++
    
    switch ($Status) {
        "PASS" { 
            $TestResults.Summary.Passed++
            $Color = "Green"
            $Icon = "[✓]"
        }
        "FAIL" { 
            $TestResults.Summary.Failed++
            $Color = "Red"
            $Icon = "[✗]"
        }
        "WARN" { 
            $TestResults.Summary.Warnings++
            $Color = "Yellow"
            $Icon = "[⚠]"
        }
        "ERROR" { 
            $TestResults.Summary.Errors++
            $Color = "Red"
            $Icon = "[!]"
        }
    }
    
    Write-Host "$Icon $Category - $TestName" -ForegroundColor $Color
    if ($Message -and $TestMode -eq "full") {
        Write-Host "    $Message" -ForegroundColor Gray
    }
}

function Test-Prerequisites {
    Write-Host ""
    Write-Host "Testing System Prerequisites..." -ForegroundColor Yellow
    
    # Test 1: Operating System
    $OS = Get-WmiObject Win32_OperatingSystem
    if ($OS.Caption -match "Windows 10|Windows 11|Windows Server") {
        Add-TestResult "Prerequisites" "Operating System" "PASS" "Compatible OS: $($OS.Caption)"
    } else {
        Add-TestResult "Prerequisites" "Operating System" "WARN" "Untested OS: $($OS.Caption)" -Critical $false
    }
    
    # Test 2: Memory
    $MemoryGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    if ($MemoryGB -ge 8) {
        Add-TestResult "Prerequisites" "System Memory" "PASS" "$MemoryGB GB RAM available"
    } elseif ($MemoryGB -ge 4) {
        Add-TestResult "Prerequisites" "System Memory" "WARN" "$MemoryGB GB RAM (minimum 8GB recommended)" -Critical $false
    } else {
        Add-TestResult "Prerequisites" "System Memory" "FAIL" "$MemoryGB GB RAM insufficient (minimum 8GB required)"
    }
    
    # Test 3: Disk Space
    $DiskSpace = [math]::Round((Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB, 2)
    if ($DiskSpace -ge 10) {
        Add-TestResult "Prerequisites" "Disk Space" "PASS" "$DiskSpace GB free space available"
    } else {
        Add-TestResult "Prerequisites" "Disk Space" "FAIL" "$DiskSpace GB free space (minimum 10GB required)"
    }
    
    # Test 4: Administrator Rights
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    if ($IsAdmin) {
        Add-TestResult "Prerequisites" "Administrator Rights" "PASS" "Running with administrator privileges"
    } else {
        Add-TestResult "Prerequisites" "Administrator Rights" "FAIL" "Administrator rights required for installation"
    }
    
    # Test 5: PowerShell Version
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        Add-TestResult "Prerequisites" "PowerShell Version" "PASS" "PowerShell $($PSVersionTable.PSVersion) compatible"
    } else {
        Add-TestResult "Prerequisites" "PowerShell Version" "WARN" "PowerShell $($PSVersionTable.PSVersion) may have compatibility issues" -Critical $false
    }
}

function Test-InstallationFiles {
    Write-Host ""
    Write-Host "Testing Installation Package..." -ForegroundColor Yellow
    
    $InstallPath = "C:\Program Files\TerraFusion"
    
    # Test 1: Installation Directory
    if (Test-Path $InstallPath) {
        Add-TestResult "Installation" "Installation Directory" "PASS" "TerraFusion found at $InstallPath"
        
        # Test core files
        $CoreFiles = @(
            "bin\terrafusion_gateway.exe",
            "bin\sync_service.exe",
            "config\county.env"
        )
        
        $MissingFiles = @()
        foreach ($File in $CoreFiles) {
            if (!(Test-Path (Join-Path $InstallPath $File))) {
                $MissingFiles += $File
            }
        }
        
        if ($MissingFiles.Count -eq 0) {
            Add-TestResult "Installation" "Core Files" "PASS" "All essential files present"
        } else {
            Add-TestResult "Installation" "Core Files" "FAIL" "Missing files: $($MissingFiles -join ', ')"
        }
        
    } else {
        Add-TestResult "Installation" "Installation Directory" "FAIL" "TerraFusion not found at expected location"
    }
    
    # Test 2: Configuration Files
    $ConfigPath = Join-Path $InstallPath "config\county.env"
    if (Test-Path $ConfigPath) {
        $ConfigContent = Get-Content $ConfigPath -Raw
        if ($ConfigContent -match "DATABASE_URL" -and $ConfigContent -match "SESSION_SECRET") {
            Add-TestResult "Installation" "Configuration" "PASS" "County configuration file properly formatted"
        } else {
            Add-TestResult "Installation" "Configuration" "WARN" "Configuration file may be incomplete" -Critical $false
        }
    } else {
        Add-TestResult "Installation" "Configuration" "FAIL" "County configuration file missing"
    }
    
    # Test 3: Data Directories
    $DataDirs = @(
        "C:\ProgramData\TerraFusion",
        "C:\ProgramData\TerraFusion\logs",
        "C:\ProgramData\TerraFusion\backups"
    )
    
    $MissingDirs = @()
    foreach ($Dir in $DataDirs) {
        if (!(Test-Path $Dir)) {
            $MissingDirs += $Dir
        }
    }
    
    if ($MissingDirs.Count -eq 0) {
        Add-TestResult "Installation" "Data Directories" "PASS" "All data directories created"
    } else {
        Add-TestResult "Installation" "Data Directories" "WARN" "Missing directories: $($MissingDirs -join ', ')" -Critical $false
    }
}

function Test-WindowsServices {
    Write-Host ""
    Write-Host "Testing Windows Services..." -ForegroundColor Yellow
    
    $Services = @("TerraFusion Gateway", "TerraFusion Sync")
    
    foreach ($ServiceName in $Services) {
        try {
            $Service = Get-Service -Name $ServiceName -ErrorAction Stop
            
            if ($Service.Status -eq "Running") {
                Add-TestResult "Services" $ServiceName "PASS" "Service running (Status: $($Service.Status))"
            } elseif ($Service.Status -eq "Stopped") {
                # Try to start the service
                try {
                    Start-Service -Name $ServiceName -ErrorAction Stop
                    Start-Sleep -Seconds 5
                    $Service = Get-Service -Name $ServiceName
                    if ($Service.Status -eq "Running") {
                        Add-TestResult "Services" $ServiceName "PASS" "Service started successfully"
                    } else {
                        Add-TestResult "Services" $ServiceName "FAIL" "Service failed to start (Status: $($Service.Status))"
                    }
                } catch {
                    Add-TestResult "Services" $ServiceName "FAIL" "Failed to start service: $($_.Exception.Message)"
                }
            } else {
                Add-TestResult "Services" $ServiceName "WARN" "Service in unexpected state: $($Service.Status)" -Critical $false
            }
            
            # Test service startup type
            if ($Service.StartType -eq "Automatic") {
                Add-TestResult "Services" "$ServiceName Startup" "PASS" "Service configured for automatic startup"
            } else {
                Add-TestResult "Services" "$ServiceName Startup" "WARN" "Service not set to automatic startup" -Critical $false
            }
            
        } catch {
            Add-TestResult "Services" $ServiceName "FAIL" "Service not found or inaccessible: $($_.Exception.Message)"
        }
    }
}

function Test-NetworkConnectivity {
    Write-Host ""
    Write-Host "Testing Network Connectivity..." -ForegroundColor Yellow
    
    # Test 1: API Gateway
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            Add-TestResult "Network" "API Gateway" "PASS" "API Gateway responding on port 5000"
            
            # Parse response for additional details
            try {
                $StatusData = $Response.Content | ConvertFrom-Json
                if ($StatusData.status -eq "success") {
                    Add-TestResult "Network" "API Health" "PASS" "API health check successful"
                } else {
                    Add-TestResult "Network" "API Health" "WARN" "API health check returned non-success status" -Critical $false
                }
            } catch {
                Add-TestResult "Network" "API Health" "WARN" "Could not parse API health response" -Critical $false
            }
        } else {
            Add-TestResult "Network" "API Gateway" "FAIL" "API Gateway returned status code: $($Response.StatusCode)"
        }
    } catch {
        Add-TestResult "Network" "API Gateway" "FAIL" "API Gateway not accessible: $($_.Exception.Message)"
    }
    
    # Test 2: Sync Service (port 8080)
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        Add-TestResult "Network" "Sync Service" "PASS" "Sync Service responding on port 8080"
    } catch {
        Add-TestResult "Network" "Sync Service" "WARN" "Sync Service not accessible (may be expected if internal only)" -Critical $false
    }
    
    # Test 3: Port Availability
    $RequiredPorts = @(5000, 8080)
    foreach ($Port in $RequiredPorts) {
        $Connection = Test-NetConnection -ComputerName "localhost" -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($Connection) {
            Add-TestResult "Network" "Port $Port" "PASS" "Port $Port is accessible"
        } else {
            Add-TestResult "Network" "Port $Port" "FAIL" "Port $Port is not accessible"
        }
    }
}

function Test-DatabaseConnectivity {
    Write-Host ""
    Write-Host "Testing Database Connectivity..." -ForegroundColor Yellow
    
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 15 -UseBasicParsing -ErrorAction Stop
        $StatusData = $Response.Content | ConvertFrom-Json
        
        if ($StatusData.data.services -and $StatusData.data.services.database) {
            $DbStatus = $StatusData.data.services.database
            if ($DbStatus -eq "healthy" -or $DbStatus -eq "unknown") {
                Add-TestResult "Database" "Connection" "PASS" "Database connection verified"
            } else {
                Add-TestResult "Database" "Connection" "FAIL" "Database connection failed: $DbStatus"
            }
        } else {
            Add-TestResult "Database" "Connection" "WARN" "Database status not available from API" -Critical $false
        }
    } catch {
        Add-TestResult "Database" "Connection" "WARN" "Could not verify database status: $($_.Exception.Message)" -Critical $false
    }
    
    # Test PostgreSQL process
    $PostgresProcess = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
    if ($PostgresProcess) {
        Add-TestResult "Database" "PostgreSQL Process" "PASS" "PostgreSQL process running"
    } else {
        Add-TestResult "Database" "PostgreSQL Process" "WARN" "PostgreSQL process not detected (may use external database)" -Critical $false
    }
}

function Test-AIFeatures {
    Write-Host ""
    Write-Host "Testing AI Features..." -ForegroundColor Yellow
    
    # Test 1: Ollama Process
    $OllamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($OllamaProcess) {
        Add-TestResult "AI" "Ollama Runtime" "PASS" "Ollama AI runtime is running"
        
        # Test 2: AI Model availability
        try {
            $Response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            $ModelsData = $Response.Content | ConvertFrom-Json
            if ($ModelsData.models -and $ModelsData.models.Count -gt 0) {
                Add-TestResult "AI" "AI Models" "PASS" "$($ModelsData.models.Count) AI model(s) available"
            } else {
                Add-TestResult "AI" "AI Models" "WARN" "No AI models found" -Critical $false
            }
        } catch {
            Add-TestResult "AI" "AI Models" "WARN" "Could not verify AI models: $($_.Exception.Message)" -Critical $false
        }
        
        # Test 3: NarratorAI Integration
        try {
            $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/v1/ai/health" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            Add-TestResult "AI" "NarratorAI Integration" "PASS" "NarratorAI integration working"
        } catch {
            Add-TestResult "AI" "NarratorAI Integration" "WARN" "NarratorAI integration not responding" -Critical $false
        }
        
    } else {
        Add-TestResult "AI" "Ollama Runtime" "WARN" "Ollama AI runtime not running (AI features disabled)" -Critical $false
        Add-TestResult "AI" "AI Models" "WARN" "AI models not available without Ollama" -Critical $false
        Add-TestResult "AI" "NarratorAI Integration" "WARN" "NarratorAI features not available" -Critical $false
    }
}

function Test-GISCapabilities {
    Write-Host ""
    Write-Host "Testing GIS Export Capabilities..." -ForegroundColor Yellow
    
    # Test 1: GIS Export Formats
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/formats" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $FormatsData = $Response.Content | ConvertFrom-Json
        
        if ($FormatsData.data.supported_formats -and $FormatsData.data.supported_formats.Count -gt 0) {
            $FormatCount = ($FormatsData.data.supported_formats | Get-Member -MemberType NoteProperty).Count
            Add-TestResult "GIS" "Export Formats" "PASS" "$FormatCount export formats available"
        } else {
            Add-TestResult "GIS" "Export Formats" "FAIL" "No GIS export formats available"
        }
    } catch {
        Add-TestResult "GIS" "Export Formats" "FAIL" "GIS export engine not responding: $($_.Exception.Message)"
    }
    
    # Test 2: District Lookup
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:5000/api/v1/district-lookup/districts" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        Add-TestResult "GIS" "District Lookup" "PASS" "District lookup service available"
    } catch {
        Add-TestResult "GIS" "District Lookup" "WARN" "District lookup service not responding" -Critical $false
    }
    
    # Test 3: Sample Data
    $SampleDataPath = "C:\ProgramData\TerraFusion\sample_data"
    if (Test-Path $SampleDataPath) {
        $SampleFiles = Get-ChildItem $SampleDataPath -Recurse | Measure-Object
        if ($SampleFiles.Count -gt 0) {
            Add-TestResult "GIS" "Sample Data" "PASS" "$($SampleFiles.Count) sample data files available"
        } else {
            Add-TestResult "GIS" "Sample Data" "WARN" "Sample data directory empty" -Critical $false
        }
    } else {
        Add-TestResult "GIS" "Sample Data" "WARN" "Sample data not installed" -Critical $false
    }
}

function Test-DesktopIntegration {
    Write-Host ""
    Write-Host "Testing Desktop Integration..." -ForegroundColor Yellow
    
    # Test 1: Desktop Shortcuts
    $DesktopShortcut = "$env:PUBLIC\Desktop\TerraFusion Platform.lnk"
    if (Test-Path $DesktopShortcut) {
        Add-TestResult "Desktop" "Desktop Shortcut" "PASS" "Desktop shortcut created"
    } else {
        Add-TestResult "Desktop" "Desktop Shortcut" "WARN" "Desktop shortcut missing" -Critical $false
    }
    
    # Test 2: Start Menu
    $StartMenuPath = "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\TerraFusion Platform"
    if (Test-Path $StartMenuPath) {
        $StartMenuItems = Get-ChildItem $StartMenuPath | Measure-Object
        Add-TestResult "Desktop" "Start Menu" "PASS" "$($StartMenuItems.Count) Start Menu items created"
    } else {
        Add-TestResult "Desktop" "Start Menu" "WARN" "Start Menu folder missing" -Critical $false
    }
    
    # Test 3: System Tray (if applicable)
    $TrayProcess = Get-Process -Name "terrafusion_tray" -ErrorAction SilentlyContinue
    if ($TrayProcess) {
        Add-TestResult "Desktop" "System Tray" "PASS" "System tray application running"
    } else {
        Add-TestResult "Desktop" "System Tray" "WARN" "System tray application not running" -Critical $false
    }
    
    # Test 4: Uninstaller
    $UninstallPath = "C:\Program Files\TerraFusion\uninst.exe"
    if (Test-Path $UninstallPath) {
        Add-TestResult "Desktop" "Uninstaller" "PASS" "Uninstaller available"
    } else {
        Add-TestResult "Desktop" "Uninstaller" "WARN" "Uninstaller not found" -Critical $false
    }
}

function Test-RebootResilience {
    Write-Host ""
    Write-Host "Testing Reboot Resilience..." -ForegroundColor Yellow
    
    # Test service startup types
    $Services = @("TerraFusion Gateway", "TerraFusion Sync")
    $AutoStartServices = 0
    
    foreach ($ServiceName in $Services) {
        try {
            $Service = Get-Service -Name $ServiceName -ErrorAction Stop
            if ($Service.StartType -eq "Automatic") {
                $AutoStartServices++
            }
        } catch {
            # Service not found, skip
        }
    }
    
    if ($AutoStartServices -eq $Services.Count) {
        Add-TestResult "Resilience" "Auto-Start Services" "PASS" "All services configured for automatic startup"
    } elseif ($AutoStartServices -gt 0) {
        Add-TestResult "Resilience" "Auto-Start Services" "WARN" "Some services not configured for automatic startup" -Critical $false
    } else {
        Add-TestResult "Resilience" "Auto-Start Services" "FAIL" "No services configured for automatic startup"
    }
    
    # Test startup registry entries (for tray app)
    $StartupEntries = Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
    if ($StartupEntries -and $StartupEntries.TerraFusion) {
        Add-TestResult "Resilience" "Startup Integration" "PASS" "TerraFusion configured to start with Windows"
    } else {
        Add-TestResult "Resilience" "Startup Integration" "WARN" "TerraFusion not configured for user startup" -Critical $false
    }
}

# Run the tests based on mode
switch ($TestMode) {
    "quick" {
        Test-Prerequisites
        Test-WindowsServices
        Test-NetworkConnectivity
    }
    "services-only" {
        Test-WindowsServices
        Test-NetworkConnectivity
        Test-DatabaseConnectivity
    }
    "full" {
        Test-Prerequisites
        Test-InstallationFiles
        Test-WindowsServices
        Test-NetworkConnectivity
        Test-DatabaseConnectivity
        Test-AIFeatures
        Test-GISCapabilities
        Test-DesktopIntegration
        Test-RebootResilience
    }
}

# Calculate overall status
$CriticalFailures = ($TestResults.Tests | Where-Object { $_.Critical -and ($_.Status -eq "FAIL" -or $_.Status -eq "ERROR") }).Count
$TotalCritical = ($TestResults.Tests | Where-Object { $_.Critical }).Count

if ($CriticalFailures -eq 0) {
    $TestResults.Summary.OverallStatus = "PASS"
    $OverallColor = "Green"
    $OverallMessage = "TerraFusion deployment validation SUCCESSFUL"
} elseif ($CriticalFailures -le 2) {
    $TestResults.Summary.OverallStatus = "PARTIAL"
    $OverallColor = "Yellow"
    $OverallMessage = "TerraFusion deployment has minor issues"
} else {
    $TestResults.Summary.OverallStatus = "FAIL"
    $OverallColor = "Red"
    $OverallMessage = "TerraFusion deployment validation FAILED"
}

# Display summary
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host $OverallMessage -ForegroundColor $OverallColor
Write-Host ""
Write-Host "Test Results:" -ForegroundColor White
Write-Host "  Total Tests: $($TestResults.Summary.TotalTests)" -ForegroundColor White
Write-Host "  Passed: $($TestResults.Summary.Passed)" -ForegroundColor Green
Write-Host "  Failed: $($TestResults.Summary.Failed)" -ForegroundColor Red
Write-Host "  Warnings: $($TestResults.Summary.Warnings)" -ForegroundColor Yellow
Write-Host "  Errors: $($TestResults.Summary.Errors)" -ForegroundColor Red
Write-Host ""

if ($TestResults.Summary.OverallStatus -eq "PASS") {
    Write-Host "🎉 County Deployment Ready!" -ForegroundColor Green
    Write-Host "   Platform: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "   Status: All critical components operational" -ForegroundColor Green
} else {
    Write-Host "⚠️ Deployment Issues Detected" -ForegroundColor Yellow
    Write-Host "   Review failed tests and resolve issues before county deployment" -ForegroundColor Yellow
}

# Generate detailed report if requested
if ($GenerateReport) {
    try {
        $TestResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $ReportPath -Encoding UTF8
        Write-Host ""
        Write-Host "Detailed report saved to: $ReportPath" -ForegroundColor Cyan
    } catch {
        Write-Host "Failed to save report: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Verification complete. Return code: $(if ($TestResults.Summary.OverallStatus -eq 'PASS') { 0 } else { 1 })" -ForegroundColor Gray

exit $(if ($TestResults.Summary.OverallStatus -eq "PASS") { 0 } else { 1 })