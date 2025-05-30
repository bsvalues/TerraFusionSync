# TerraFusion Platform Azure Quick Start Script
# This script provides a quick way to get started with Azure deployment

# Display welcome message
Write-Host @"
======================================================
   TerraFusion Platform Azure Deployment Quick Start
======================================================

This script will guide you through setting up TerraFusion
on Azure without needing Docker or local containers.

Prerequisites:
- Azure account with appropriate permissions
- Azure PowerShell and Azure CLI installed
- Local copy of the TerraFusion Platform code

"@ -ForegroundColor Cyan

# Check for Azure PowerShell modules
if (-not (Get-Module -ListAvailable -Name Az)) {
    Write-Host "Azure PowerShell module not found. Do you want to install it now? (Y/N)" -ForegroundColor Yellow
    $install = Read-Host
    if ($install -eq 'Y' -or $install -eq 'y') {
        Write-Host "Installing Azure PowerShell module..." -ForegroundColor Green
        Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force
    } else {
        Write-Host "Azure PowerShell module is required. Please install it and run this script again." -ForegroundColor Red
        exit
    }
}

# Check for Azure CLI
try {
    $azCliVersion = az --version
    Write-Host "Azure CLI found: $azCliVersion" -ForegroundColor Green
} catch {
    Write-Host "Azure CLI not found. Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit
}

# Login to Azure
Write-Host "Please login to your Azure account..." -ForegroundColor Green
Connect-AzAccount

# Set subscription context
$subscriptionId = "b345d747-5953-4468-a1c7-18164d6f26e4"  # Default for this project
Write-Host "Setting subscription context to: $subscriptionId" -ForegroundColor Green
Set-AzContext -SubscriptionId $subscriptionId

# Ask for deployment options
Write-Host "Please select deployment options:" -ForegroundColor Cyan
Write-Host "1. Full deployment (infrastructure + code)" -ForegroundColor White
Write-Host "2. Infrastructure only" -ForegroundColor White
Write-Host "3. Code deployment only (requires existing infrastructure)" -ForegroundColor White
$option = Read-Host "Enter option (1-3)"

switch ($option) {
    "1" {
        # Full deployment
        Write-Host "Starting full deployment..." -ForegroundColor Green
        & ./azure-migration.ps1
        & ./deploy-to-azure.ps1 -SkipInfrastructureSetup
    }
    "2" {
        # Infrastructure only
        Write-Host "Setting up infrastructure only..." -ForegroundColor Green
        & ./azure-migration.ps1
    }
    "3" {
        # Code deployment only
        Write-Host "Deploying code only (using existing infrastructure)..." -ForegroundColor Green
        & ./deploy-to-azure.ps1 -SkipInfrastructureSetup
    }
    default {
        Write-Host "Invalid option. Please run the script again and select a valid option." -ForegroundColor Red
        exit
    }
}

# Display completion message
Write-Host @"

======================================================
   Deployment Process Complete!
======================================================

Your TerraFusion Platform should now be available on Azure.

Next steps:
1. Visit the Azure Portal to view your resources
2. Check the API Gateway URL for your application
3. Monitor application performance in Application Insights

For more information, see the AZURE_DEPLOYMENT.md file.

"@ -ForegroundColor Green