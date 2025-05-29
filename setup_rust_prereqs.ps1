# TerraFusion Platform - Rust Prerequisites Setup
# This script automatically installs everything needed for TerraFusion Rust services
# Designed for county IT departments with minimal Rust experience

Write-Host "========================================" -ForegroundColor Green
Write-Host "TerraFusion Platform - Rust Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[!] This script requires administrator privileges." -ForegroundColor Red
    Write-Host "    Please right-click and 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[✓] Running with administrator privileges" -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Step 1: Install Visual Studio Build Tools (required for Rust)
Write-Host "[1/5] Checking Visual Studio Build Tools..." -ForegroundColor Yellow

if (Test-CommandExists "cl") {
    Write-Host "[✓] Visual Studio Build Tools already installed" -ForegroundColor Green
} else {
    Write-Host "[!] Installing Visual Studio Build Tools..." -ForegroundColor Yellow
    Write-Host "    This may take 10-15 minutes..." -ForegroundColor Cyan
    
    # Download VS Build Tools installer
    $vsUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    $vsInstaller = "$env:TEMP\vs_buildtools.exe"
    
    try {
        Invoke-WebRequest -Uri $vsUrl -OutFile $vsInstaller
        
        # Install with required components for Rust
        Start-Process -FilePath $vsInstaller -ArgumentList "--quiet", "--wait", "--add", "Microsoft.VisualStudio.Workload.VCTools", "--add", "Microsoft.VisualStudio.Component.Windows10SDK.19041" -Wait
        
        Write-Host "[✓] Visual Studio Build Tools installed" -ForegroundColor Green
        
        # Clean up
        Remove-Item $vsInstaller -Force
    } catch {
        Write-Host "[✗] Failed to install Visual Studio Build Tools" -ForegroundColor Red
        Write-Host "    Please install manually from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Yellow
        Read-Host "Press Enter to continue anyway"
    }
}

Write-Host ""

# Step 2: Install Rust
Write-Host "[2/5] Checking Rust installation..." -ForegroundColor Yellow

if (Test-CommandExists "rustc") {
    $rustVersion = rustc --version
    Write-Host "[✓] Rust already installed: $rustVersion" -ForegroundColor Green
} else {
    Write-Host "[!] Installing Rust..." -ForegroundColor Yellow
    
    # Download and install rustup
    $rustupUrl = "https://win.rustup.rs/x86_64"
    $rustupInstaller = "$env:TEMP\rustup-init.exe"
    
    try {
        Invoke-WebRequest -Uri $rustupUrl -OutFile $rustupInstaller
        
        # Install Rust with default settings
        Start-Process -FilePath $rustupInstaller -ArgumentList "-y" -Wait
        
        # Add Rust to PATH for current session
        $env:PATH += ";$env:USERPROFILE\.cargo\bin"
        
        Write-Host "[✓] Rust installed successfully" -ForegroundColor Green
        
        # Clean up
        Remove-Item $rustupInstaller -Force
    } catch {
        Write-Host "[✗] Failed to install Rust" -ForegroundColor Red
        Write-Host "    Please install manually from: https://rustup.rs/" -ForegroundColor Yellow
        Read-Host "Press Enter to continue anyway"
    }
}

Write-Host ""

# Step 3: Install Git (if not present)
Write-Host "[3/5] Checking Git installation..." -ForegroundColor Yellow

if (Test-CommandExists "git") {
    $gitVersion = git --version
    Write-Host "[✓] Git already installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "[!] Installing Git..." -ForegroundColor Yellow
    
    # Install Git using winget if available
    if (Test-CommandExists "winget") {
        try {
            winget install --id Git.Git -e --source winget --silent
            Write-Host "[✓] Git installed via winget" -ForegroundColor Green
        } catch {
            Write-Host "[!] Please install Git manually from: https://git-scm.com/download/win" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[!] Please install Git manually from: https://git-scm.com/download/win" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Install additional Rust components for TerraFusion
Write-Host "[4/5] Installing TerraFusion Rust components..." -ForegroundColor Yellow

if (Test-CommandExists "rustc") {
    try {
        # Update Rust to latest stable
        rustup update stable
        
        # Install additional targets and components
        rustup target add x86_64-pc-windows-msvc
        rustup component add rustfmt clippy
        
        # Install cargo-watch for development (optional)
        cargo install cargo-watch --quiet
        
        Write-Host "[✓] Rust components configured for TerraFusion" -ForegroundColor Green
    } catch {
        Write-Host "[!] Some Rust components may not have installed correctly" -ForegroundColor Yellow
        Write-Host "    TerraFusion should still work with basic Rust installation" -ForegroundColor Cyan
    }
} else {
    Write-Host "[!] Skipping Rust components (Rust not found)" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Verify installation
Write-Host "[5/5] Verifying installation..." -ForegroundColor Yellow

$allGood = $true

# Check Rust
if (Test-CommandExists "rustc") {
    $rustVersion = rustc --version
    Write-Host "[✓] Rust: $rustVersion" -ForegroundColor Green
} else {
    Write-Host "[✗] Rust not found" -ForegroundColor Red
    $allGood = $false
}

# Check Cargo
if (Test-CommandExists "cargo") {
    $cargoVersion = cargo --version
    Write-Host "[✓] Cargo: $cargoVersion" -ForegroundColor Green
} else {
    Write-Host "[✗] Cargo not found" -ForegroundColor Red
    $allGood = $false
}

# Check Git
if (Test-CommandExists "git") {
    $gitVersion = git --version
    Write-Host "[✓] Git: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "[!] Git not found (optional but recommended)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green

if ($allGood) {
    Write-Host "✅ TerraFusion Rust Prerequisites Setup Complete!" -ForegroundColor Green
    Write-Host "" 
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Close this PowerShell window" -ForegroundColor White
    Write-Host "2. Run 'run_all_rust.bat' to start TerraFusion services" -ForegroundColor White
    Write-Host "3. Access the platform at http://localhost:5000" -ForegroundColor White
} else {
    Write-Host "⚠️  Setup completed with warnings" -ForegroundColor Yellow
    Write-Host "   Some components may need manual installation" -ForegroundColor Yellow
    Write-Host "   TerraFusion may fall back to Python services" -ForegroundColor Cyan
}

Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Create a verification script for later use
$verificationScript = @"
# TerraFusion Environment Verification
Write-Host "TerraFusion Environment Check:" -ForegroundColor Green
if (Get-Command rustc -ErrorAction SilentlyContinue) { 
    Write-Host "✓ Rust: $(rustc --version)" -ForegroundColor Green 
} else { 
    Write-Host "✗ Rust not found" -ForegroundColor Red 
}
if (Get-Command cargo -ErrorAction SilentlyContinue) { 
    Write-Host "✓ Cargo: $(cargo --version)" -ForegroundColor Green 
} else { 
    Write-Host "✗ Cargo not found" -ForegroundColor Red 
}
if (Get-Command git -ErrorAction SilentlyContinue) { 
    Write-Host "✓ Git: $(git --version)" -ForegroundColor Green 
} else { 
    Write-Host "! Git not found" -ForegroundColor Yellow 
}
"@

$verificationScript | Out-File -FilePath "verify_terrafusion_env.ps1" -Encoding UTF8
Write-Host "Created verify_terrafusion_env.ps1 for future environment checks" -ForegroundColor Cyan

Read-Host "Press Enter to complete setup"