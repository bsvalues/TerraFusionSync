# TerraFusion Platform Azure Migration Script
# This script creates all necessary Azure resources for the TerraFusion Platform

# Variables for the deployment
$resourceGroupName = "TerraFusionResourceGroup"
$location = "WestUS2"
$appInsightsName = "TerraFusionInsights"
$appServicePlanName = "TerraFusionPlan"
$webAppName = "TerraFusionGateway"
$dbServerName = "terrafusion-db"
$dbName = "terrafusiondb"
$dbAdminUser = "adminuser"

# Login to Azure
Write-Host "Please login to your Azure account..." -ForegroundColor Green
Connect-AzAccount

# Set subscription context
$subscriptionId = "b345d747-5953-4468-a1c7-18164d6f26e4"
Set-AzContext -SubscriptionId $subscriptionId

# Create Resource Group
Write-Host "Creating Resource Group: $resourceGroupName..." -ForegroundColor Green
New-AzResourceGroup -Name $resourceGroupName -Location $location -Force

# Create Application Insights
Write-Host "Creating Application Insights: $appInsightsName..." -ForegroundColor Green
$appInsights = New-AzApplicationInsights -Name $appInsightsName -ResourceGroupName $resourceGroupName -Location $location -Kind web
$instrumentationKey = $appInsights.InstrumentationKey
Write-Host "Application Insights instrumentation key: $instrumentationKey" -ForegroundColor Yellow
Write-Host "Store this key securely, you will need it to configure your application." -ForegroundColor Yellow

# Create App Service Plan
Write-Host "Creating App Service Plan: $appServicePlanName..." -ForegroundColor Green
New-AzAppServicePlan -Name $appServicePlanName -ResourceGroupName $resourceGroupName -Location $location -Tier "Basic" -WorkerSize "Small" -NumberofWorkers 1

# Create Web App
Write-Host "Creating Web App: $webAppName..." -ForegroundColor Green
New-AzWebApp -Name $webAppName -ResourceGroupName $resourceGroupName -Location $location -AppServicePlan $appServicePlanName -RuntimeStack "PYTHON|3.9"

# Create Database Server
Write-Host "Creating PostgreSQL Server: $dbServerName..." -ForegroundColor Green
$securePassword = Read-Host "Enter a password for the database administrator" -AsSecureString
New-AzPostgreSqlServer -ResourceGroupName $resourceGroupName -Name $dbServerName -Location $location -AdministratorUserName $dbAdminUser -AdministratorLoginPassword $securePassword -Sku "GP_Gen5_2"

# Create Database
Write-Host "Creating Database: $dbName..." -ForegroundColor Green
New-AzPostgreSqlDatabase -ResourceGroupName $resourceGroupName -ServerName $dbServerName -Name $dbName

# Configure firewall rule to allow Azure services
Write-Host "Configuring firewall rule to allow Azure services..." -ForegroundColor Green
New-AzPostgreSqlFirewallRule -ResourceGroupName $resourceGroupName -ServerName $dbServerName -Name "AllowAllAzureIPs" -StartIPAddress "0.0.0.0" -EndIPAddress "0.0.0.0"

# Configure connection string for the Web App
Write-Host "Configuring connection string for the Web App..." -ForegroundColor Green
$connectionString = "postgresql://$dbAdminUser@$dbServerName.postgres.database.azure.com:5432/$dbName"
Set-AzWebApp -ResourceGroupName $resourceGroupName -Name $webAppName -ConnectionStrings @{DATABASE_URL = @{Type = "PostgreSQL"; Value = $connectionString}}

# Set Application Insights environment variable
Write-Host "Setting Application Insights instrumentation key environment variable..." -ForegroundColor Green
$appSettings = @{
    "APPINSIGHTS_INSTRUMENTATIONKEY" = $instrumentationKey
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = "InstrumentationKey=$instrumentationKey"
}
Set-AzWebApp -ResourceGroupName $resourceGroupName -Name $webAppName -AppSettings $appSettings

Write-Host "Azure infrastructure setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Update your application code with App Insights integration" -ForegroundColor Green
Write-Host "2. Deploy your application code to the Azure Web App" -ForegroundColor Green
Write-Host "3. Configure CI/CD using GitHub Actions or Azure DevOps" -ForegroundColor Green