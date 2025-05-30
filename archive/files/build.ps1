# TerraFusion Platform - Enterprise Build Script
# Builds optimized release binaries and creates Windows installer package

param(
    [string]$Configuration = "Release",
    [string]$CountyId = "example-county",
    [string]$Version = "1.0.0",
    [switch]$SkipTests = $false,
    [switch]$CreateInstaller = $true,
    [switch]$SignBinaries = $false
)

# Build configuration
$ErrorActionPreference = "Stop"
$BuildDir = "target\release"
$InstallerDir = "installer"
$OutputDir = "dist"

Write-Host "🚀 TerraFusion Platform - Enterprise Build" -ForegroundColor Green
Write-Host "Configuration: $Configuration" -ForegroundColor Cyan
Write-Host "Target County: $CountyId" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Cyan

# Clean previous builds
Write-Host "`n🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path $OutputDir) { Remove-Item $OutputDir -Recurse -Force }
if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Set optimization environment variables
$env:CARGO_PROFILE_RELEASE_LTO = "true"
$env:CARGO_PROFILE_RELEASE_CODEGEN_UNITS = "1"
$env:CARGO_PROFILE_RELEASE_PANIC = "abort"
$env:CARGO_PROFILE_RELEASE_STRIP = "symbols"

# Build all Rust components
Write-Host "`n🔧 Building Rust components..." -ForegroundColor Yellow

$Services = @(
    @{Name="API Gateway"; Path="terrarust/api_gateway"; Binary="terrafusion-api-gateway.exe"},
    @{Name="Sync Service"; Path="terrarust/sync_service"; Binary="terrafusion-sync-service.exe"},
    @{Name="GIS Export Service"; Path="terrarust/gis_export"; Binary="terrafusion-gis-export.exe"}
)

foreach ($service in $Services) {
    Write-Host "  Building $($service.Name)..." -ForegroundColor Cyan
    Set-Location $service.Path
    cargo build --release --target x86_64-pc-windows-msvc
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build $($service.Name)"
        exit 1
    }
    
    # Copy binary to output directory
    Copy-Item "target\release\$($service.Binary)" "..\..\$OutputDir\" -Force
    Set-Location ..\..
}

# Build supporting utilities
Write-Host "`n🛠️ Building supporting utilities..." -ForegroundColor Yellow

# Build setup utility
Write-Host "  Building setup utility..." -ForegroundColor Cyan
Set-Location terrarust\setup_utility
cargo build --release --target x86_64-pc-windows-msvc
Copy-Item "target\release\terrafusion-setup.exe" "..\..\$OutputDir\" -Force
Set-Location ..\..

# Build management console
Write-Host "  Building management console..." -ForegroundColor Cyan
Set-Location terrarust\management_console
cargo build --release --target x86_64-pc-windows-msvc
Copy-Item "target\release\terrafusion-console.exe" "..\..\$OutputDir\" -Force
Set-Location ..\..

# Build Windows service wrapper
Write-Host "  Building Windows service wrapper..." -ForegroundColor Cyan
Set-Location terrarust\service_wrapper
cargo build --release --target x86_64-pc-windows-msvc
Copy-Item "target\release\terrafusion-service.exe" "..\..\$OutputDir\" -Force
Set-Location ..\..

# Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Host "`n🧪 Running tests..." -ForegroundColor Yellow
    Set-Location terrarust
    cargo test --workspace --release
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tests failed"
        exit 1
    }
    Set-Location ..
}

# Code signing (if enabled)
if ($SignBinaries) {
    Write-Host "`n🔐 Code signing binaries..." -ForegroundColor Yellow
    $CertThumbprint = $env:CODE_SIGNING_CERT_THUMBPRINT
    if (-not $CertThumbprint) {
        Write-Warning "CODE_SIGNING_CERT_THUMBPRINT not set, skipping code signing"
    } else {
        Get-ChildItem "$OutputDir\*.exe" | ForEach-Object {
            Write-Host "  Signing $($_.Name)..." -ForegroundColor Cyan
            signtool sign /sha1 $CertThumbprint /t http://timestamp.digicert.com /fd SHA256 $_.FullName
        }
    }
}

# Prepare installer components
Write-Host "`n📦 Preparing installer components..." -ForegroundColor Yellow

# Copy PostgreSQL portable
$PostgreSQLDir = "$OutputDir\postgresql"
New-Item -ItemType Directory -Path $PostgreSQLDir -Force | Out-Null
# TODO: Download and extract PostgreSQL portable if not present

# Copy web interface assets
$WebDir = "$OutputDir\web"
New-Item -ItemType Directory -Path $WebDir -Force | Out-Null
Copy-Item "terrarust\api_gateway\static\*" $WebDir -Recurse -Force

# Copy configuration templates
$ConfigDir = "$OutputDir\config"
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
Copy-Item "installer\config\*" $ConfigDir -Recurse -Force

# Generate county-specific configuration
$CountyConfigPath = "$ConfigDir\counties\$CountyId.toml"
$CountyTemplate = Get-Content "$ConfigDir\county-template.toml" -Raw
$CountyConfig = $CountyTemplate -replace '\{\{COUNTY_ID\}\}', $CountyId
$CountyConfig = $CountyConfig -replace '\{\{VERSION\}\}', $Version
New-Item -ItemType Directory -Path "$ConfigDir\counties" -Force | Out-Null
Set-Content -Path $CountyConfigPath -Value $CountyConfig

# Create installer (if enabled)
if ($CreateInstaller) {
    Write-Host "`n📀 Creating Windows installer..." -ForegroundColor Yellow
    
    # Check for WiX Toolset
    $WixPath = "${env:ProgramFiles(x86)}\WiX Toolset v3.11\bin"
    if (-not (Test-Path "$WixPath\candle.exe")) {
        Write-Warning "WiX Toolset not found. Please install WiX Toolset v3.11 or later."
        Write-Host "Download from: https://wixtoolset.org/releases/" -ForegroundColor Cyan
    } else {
        # Compile WiX source
        $WixVars = @(
            "-dBuildOutputDir=$((Get-Location).Path)\$OutputDir",
            "-dPostgreSQLDir=$((Get-Location).Path)\$PostgreSQLDir",
            "-dVersion=$Version",
            "-dCountyId=$CountyId"
        )
        
        & "$WixPath\candle.exe" -ext WixUtilExtension -out "$OutputDir\TerraFusion.wixobj" @WixVars "$InstallerDir\TerraFusion.wxs"
        
        if ($LASTEXITCODE -eq 0) {
            # Link installer
            & "$WixPath\light.exe" -ext WixUtilExtension -out "$OutputDir\TerraFusion-$Version-$CountyId.msi" "$OutputDir\TerraFusion.wixobj"
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Installer created: TerraFusion-$Version-$CountyId.msi" -ForegroundColor Green
                
                # Sign installer
                if ($SignBinaries -and $CertThumbprint) {
                    Write-Host "  Signing installer..." -ForegroundColor Cyan
                    signtool sign /sha1 $CertThumbprint /t http://timestamp.digicert.com /fd SHA256 "$OutputDir\TerraFusion-$Version-$CountyId.msi"
                }
            } else {
                Write-Error "Failed to create installer"
            }
        } else {
            Write-Error "Failed to compile WiX source"
        }
    }
}

# Generate deployment documentation
Write-Host "`n📋 Generating deployment documentation..." -ForegroundColor Yellow
$DeploymentGuide = @"
# TerraFusion Platform - Deployment Guide

## System Requirements
- Windows Server 2016+ or Windows 10+ (64-bit)
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space
- Network connectivity for county systems

## Installation
1. Run TerraFusion-$Version-$CountyId.msi as Administrator
2. Follow the installation wizard
3. Configure county-specific settings
4. Access web interface at http://localhost:8000

## County Configuration
County ID: $CountyId
Version: $Version
Build Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Support
- Documentation: https://docs.terrafusion.com
- Support Email: support@terrafusion.com
- Phone: 1-800-TERRA-FUSION

Generated by TerraFusion Build System
"@

Set-Content -Path "$OutputDir\DEPLOYMENT_GUIDE.txt" -Value $DeploymentGuide

# Create deployment package
Write-Host "`n📁 Creating deployment package..." -ForegroundColor Yellow
$PackageName = "TerraFusion-Platform-$Version-$CountyId"
$PackagePath = "$OutputDir\$PackageName.zip"

if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
    Compress-Archive -Path "$OutputDir\*" -DestinationPath $PackagePath -Force
    Write-Host "✅ Deployment package created: $PackageName.zip" -ForegroundColor Green
}

# Summary
Write-Host "`n🎉 Build completed successfully!" -ForegroundColor Green
Write-Host "Build artifacts:" -ForegroundColor Cyan
Get-ChildItem $OutputDir -Name | ForEach-Object { Write-Host "  $_" -ForegroundColor White }

$BuildSize = (Get-ChildItem $OutputDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "`nTotal size: $([math]::Round($BuildSize, 2)) MB" -ForegroundColor Cyan

Write-Host "`n🚀 Ready for county deployment!" -ForegroundColor Green