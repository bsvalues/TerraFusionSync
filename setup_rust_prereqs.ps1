# TerraFusion Platform - Prerequisites Setup Script
# Installs Rust, Visual C++ Build Tools, and Python dependencies
# For first-time Windows deployment to county IT staff

Write-Host ""
Write-Host "========================================================"
Write-Host "  TerraFusion Platform - Prerequisites Setup"
Write-Host "========================================================"
Write-Host ""

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as administrator. Some installations may fail." -ForegroundColor Yellow
    Write-Host "For best results, right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check Python installation
Write-Host "Checking Python installation..."
if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Installing Python 3.11..." -ForegroundColor Red
    
    # Download and install Python
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    Write-Host "Downloading Python installer..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    
    Write-Host "Installing Python (this may take a few minutes)..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Remove-Item $pythonInstaller -Force
    Write-Host "✓ Python installed successfully" -ForegroundColor Green
}

# Check Rust installation
Write-Host ""
Write-Host "Checking Rust installation..."
if (Test-Command rustc) {
    $rustVersion = rustc --version 2>&1
    Write-Host "✓ Found: $rustVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Rust not found. Installing Rust..." -ForegroundColor Red
    
    # Download and install Rust
    $rustUrl = "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe"
    $rustInstaller = "$env:TEMP\rustup-init.exe"
    
    Write-Host "Downloading Rust installer..."
    Invoke-WebRequest -Uri $rustUrl -OutFile $rustInstaller
    
    Write-Host "Installing Rust (this may take several minutes)..."
    Start-Process -FilePath $rustInstaller -ArgumentList "-y" -Wait
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Remove-Item $rustInstaller -Force
    Write-Host "✓ Rust installed successfully" -ForegroundColor Green
}

# Check Visual Studio Build Tools
Write-Host ""
Write-Host "Checking Visual Studio Build Tools..."
$vsBuildTools = Get-ChildItem "C:\Program Files*\Microsoft Visual Studio\*\BuildTools\MSBuild\Current\Bin\MSBuild.exe" -ErrorAction SilentlyContinue
if ($vsBuildTools) {
    Write-Host "✓ Visual Studio Build Tools found" -ForegroundColor Green
} else {
    Write-Host "✗ Visual Studio Build Tools not found. Installing..." -ForegroundColor Red
    
    # Download and install VS Build Tools
    $vsUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    $vsInstaller = "$env:TEMP\vs_buildtools.exe"
    
    Write-Host "Downloading Visual Studio Build Tools..."
    Invoke-WebRequest -Uri $vsUrl -OutFile $vsInstaller
    
    Write-Host "Installing Visual Studio Build Tools (this will take 10-15 minutes)..."
    Write-Host "The installer will open - please select 'C++ build tools' workload"
    Start-Process -FilePath $vsInstaller -ArgumentList "--quiet", "--wait", "--add", "Microsoft.VisualStudio.Workload.VCTools" -Wait
    
    Remove-Item $vsInstaller -Force
    Write-Host "✓ Visual Studio Build Tools installed" -ForegroundColor Green
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..."
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Some Python dependencies may have failed (this is normal if requirements.txt doesn't exist)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not install Python dependencies (requirements.txt may not exist)" -ForegroundColor Yellow
}

# Create basic environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating basic environment configuration..."
    @"
# TerraFusion Platform Environment Variables
DATABASE_URL=postgresql://postgres:password@localhost:5432/terrafusion
SESSION_SECRET=your-session-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=true
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ Basic .env file created" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================"
Write-Host "  Prerequisites Setup Complete!"
Write-Host "========================================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Configure your database connection in .env file"
Write-Host "2. Run: run_all_rust.bat to start all services"
Write-Host "3. Open: http://localhost:5000/dashboard"
Write-Host ""
Write-Host "Press any key to continue..."
Read-Host