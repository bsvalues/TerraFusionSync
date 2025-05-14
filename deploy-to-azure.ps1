# TerraFusion Platform Azure Deployment Script
# This script deploys the TerraFusion Platform to Azure Web Apps

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "TerraFusionResourceGroup",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "./azure-webapp-config.json",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipInfrastructureSetup
)

# Import configuration
Write-Host "Loading configuration from $ConfigFile" -ForegroundColor Cyan
$config = Get-Content -Path $ConfigFile | ConvertFrom-Json

# Login to Azure
Write-Host "Please login to your Azure account..." -ForegroundColor Green
Connect-AzAccount

# Set subscription context
$subscriptionId = "b345d747-5953-4468-a1c7-18164d6f26e4"
Set-AzContext -SubscriptionId $subscriptionId

# Create infrastructure if not skipped
if (-not $SkipInfrastructureSetup) {
    # Run the infrastructure setup script
    Write-Host "Setting up Azure infrastructure..." -ForegroundColor Cyan
    & ./azure-migration.ps1 -ResourceGroupName $ResourceGroupName
}

# Generate a deployment package
Write-Host "Generating deployment package..." -ForegroundColor Cyan
$tempFolder = Join-Path $env:TEMP "TerraFusionDeploy"
New-Item -ItemType Directory -Force -Path $tempFolder | Out-Null

# Create or update requirements.txt with Azure-specific dependencies
$requirementsPath = "./requirements.txt"
$azureRequirements = @(
    "opencensus-ext-azure",
    "opencensus-ext-flask",
    "opencensus-ext-fastapi",
    "opencensus-ext-requests",
    "azure-identity",
    "azure-keyvault-secrets"
)

if (Test-Path $requirementsPath) {
    $currentRequirements = Get-Content $requirementsPath
    foreach ($req in $azureRequirements) {
        if ($currentRequirements -notcontains $req) {
            Add-Content -Path $requirementsPath -Value $req
        }
    }
} else {
    $azureRequirements | Out-File -FilePath $requirementsPath
}

# Create a web.config file for API Gateway
$webConfigContent = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="D:\home\Python39\python.exe|D:\home\Python39\wfastcgi.py" resourceType="Unspecified" requireAccess="Script" />
    </handlers>
    <rewrite>
      <rules>
        <rule name="Static Files" stopProcessing="true">
          <match url="^static/.*" ignoreCase="true" />
          <action type="Rewrite" url="{R:0}" appendQueryString="true" />
        </rule>
        <rule name="All Requests" stopProcessing="true">
          <match url="(.*)" ignoreCase="true" />
          <action type="Rewrite" url="app_azure.py/{R:1}" appendQueryString="true" />
        </rule>
      </rules>
    </rewrite>
    <httpErrors errorMode="Detailed"></httpErrors>
  </system.webServer>
  <appSettings>
    <add key="PYTHONPATH" value="D:\home\site\wwwroot" />
    <add key="WSGI_HANDLER" value="app_azure.app" />
    <add key="WSGI_LOG" value="D:\home\LogFiles\wfastcgi.log" />
  </appSettings>
</configuration>
"@
$webConfigContent | Out-File -FilePath "./web.config" -Encoding utf8

# Deploy API Gateway
Write-Host "Deploying API Gateway..." -ForegroundColor Cyan
$apiGatewayName = $config.apiGateway.appName

# Get the API Gateway's publish profile
$publishProfile = [System.Convert]::ToBase64String(
    [System.Text.Encoding]::UTF8.GetBytes(
        (Get-AzWebAppPublishingProfile -ResourceGroupName $ResourceGroupName -Name $apiGatewayName)
    )
)

# Use Azure CLI to deploy
az webapp deployment source config-zip -g $ResourceGroupName -n $apiGatewayName --src ./deploy.zip

# Deploy SyncService
Write-Host "Deploying SyncService..." -ForegroundColor Cyan
$syncServiceName = $config.syncService.appName

# Get the SyncService's publish profile
$publishProfile = [System.Convert]::ToBase64String(
    [System.Text.Encoding]::UTF8.GetBytes(
        (Get-AzWebAppPublishingProfile -ResourceGroupName $ResourceGroupName -Name $syncServiceName)
    )
)

# Use Azure CLI to deploy
az webapp deployment source config-zip -g $ResourceGroupName -n $syncServiceName --src ./deploy.zip

# Configure web app settings
Write-Host "Configuring web app settings..." -ForegroundColor Cyan

# API Gateway settings
$apiGatewaySettings = @{}
foreach ($key in $config.applicationConfiguration.PSObject.Properties.Name) {
    $apiGatewaySettings[$key] = $config.applicationConfiguration.$key
}
foreach ($key in $config.apiGateway.appSettings.PSObject.Properties.Name) {
    $apiGatewaySettings[$key] = $config.apiGateway.appSettings.$key
}
$apiGatewaySettings["SYNC_SERVICE_URL"] = "https://$syncServiceName.azurewebsites.net"

Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $apiGatewayName -AppSettings $apiGatewaySettings

# SyncService settings
$syncServiceSettings = @{}
foreach ($key in $config.applicationConfiguration.PSObject.Properties.Name) {
    $syncServiceSettings[$key] = $config.applicationConfiguration.$key
}
foreach ($key in $config.syncService.appSettings.PSObject.Properties.Name) {
    $syncServiceSettings[$key] = $config.syncService.appSettings.$key
}
$syncServiceSettings["API_GATEWAY_URL"] = "https://$apiGatewayName.azurewebsites.net"

Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $syncServiceName -AppSettings $syncServiceSettings

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "API Gateway URL: https://$apiGatewayName.azurewebsites.net" -ForegroundColor Yellow
Write-Host "SyncService URL: https://$syncServiceName.azurewebsites.net" -ForegroundColor Yellow