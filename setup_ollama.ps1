# TerraFusion Platform - Ollama AI Integration Setup
# Run this script as Administrator to enable local AI capabilities

Write-Host "🧠 TerraFusion Ollama AI Integration Setup" -ForegroundColor Cyan
Write-Host "Setting up local AI capabilities for your platform..." -ForegroundColor White

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# Create temp directory
$tempDir = "$env:TEMP\TerraFusion_Ollama"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

try {
    # Download Ollama installer
    Write-Host "📥 Downloading Ollama installer..." -ForegroundColor Yellow
    $installerUrl = "https://ollama.ai/download/windows"
    $installerPath = "$tempDir\OllamaSetup.exe"
    
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✅ Ollama installer downloaded" -ForegroundColor Green
    
    # Install Ollama
    Write-Host "🛠️ Installing Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath $installerPath -Args "/S" -Wait
    Write-Host "✅ Ollama installed successfully" -ForegroundColor Green
    
    # Add Ollama to PATH if not already there
    $ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama"
    if (Test-Path $ollamaPath) {
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($currentPath -notlike "*$ollamaPath*") {
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$ollamaPath", "User")
            Write-Host "✅ Ollama added to PATH" -ForegroundColor Green
        }
    }
    
    # Start Ollama service
    Write-Host "🚀 Starting Ollama service..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -Args "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 10
    Write-Host "✅ Ollama service started" -ForegroundColor Green
    
    # Pull Llama3 model
    Write-Host "🧠 Downloading Llama3 model (this may take several minutes)..." -ForegroundColor Yellow
    $pullProcess = Start-Process -FilePath "ollama" -Args "pull llama3" -NoNewWindow -PassThru -Wait
    
    if ($pullProcess.ExitCode -eq 0) {
        Write-Host "✅ Llama3 model downloaded successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Model download had issues, but Ollama is ready" -ForegroundColor Yellow
    }
    
    # Test Ollama connection
    Write-Host "🔗 Testing Ollama connection..." -ForegroundColor Yellow
    try {
        $testResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -UseBasicParsing -TimeoutSec 10
        if ($testResponse.StatusCode -eq 200) {
            Write-Host "✅ Ollama is responding on localhost:11434" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ Ollama service may need a moment to fully start" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Ollama AI Integration Complete!" -ForegroundColor Green
    Write-Host "Your TerraFusion platform can now use local AI capabilities" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Restart your TerraFusion platform" -ForegroundColor White
    Write-Host "2. The NarratorAI service will automatically connect to Ollama" -ForegroundColor White
    Write-Host "3. Test AI features in your dashboard" -ForegroundColor White
    Write-Host "4. Run 'python test_ai_integration.py' to verify everything works" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error during setup: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again" -ForegroundColor Yellow
} finally {
    # Cleanup
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Press Enter to continue..." -ForegroundColor Gray
Read-Host