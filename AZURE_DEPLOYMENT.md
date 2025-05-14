# TerraFusion Platform Azure Deployment Guide

This guide details the process for deploying the TerraFusion Platform to Microsoft Azure, eliminating the need for Docker or other containerization technologies that may be restricted in the County network.

## Prerequisites

1. **Azure Account with Admin Access**
   - Subscription ID: b345d747-5953-4468-a1c7-18164d6f26e4
   - Administrative rights to create resources

2. **Azure PowerShell Module**
   ```powershell
   # Install Azure PowerShell module if not already installed
   Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force
   ```

3. **Azure CLI**
   - Download and install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

## Deployment Process

### Step 1: Clone the Repository
Ensure you have the latest version of the TerraFusion Platform code on your local machine.

### Step 2: Set Up Azure Infrastructure
Run the Azure infrastructure setup script:

```powershell
# Navigate to the project directory
cd path/to/terrafusion-platform

# Run the infrastructure setup script
./azure-migration.ps1
```

This script will:
- Create a resource group for TerraFusion
- Set up Application Insights for monitoring
- Create App Service Plan for web applications
- Create Web Apps for the API Gateway and SyncService
- Create a PostgreSQL database
- Configure firewall rules and connection strings

### Step 3: Update Application Code
The repository includes Azure-ready versions of the main application files:

- `app_azure.py`: Azure-integrated version of the API Gateway
- `syncservice_azure.py`: Azure-integrated version of the SyncService
- `app_insights_integration.py`: Helper module for Application Insights integration

These files include all the necessary modifications to run in Azure App Service with Application Insights monitoring.

### Step 4: Deploy to Azure
Use the deployment script to push the code to Azure:

```powershell
# Deploy using the deployment script
./deploy-to-azure.ps1 -SkipInfrastructureSetup
```

The script will:
- Package the application
- Upload it to Azure Web Apps
- Configure environment variables
- Set up connection strings

### Step 5: Verify Deployment
After deployment, verify that the services are running correctly:

1. **API Gateway**: Visit https://terrafusiongateway.azurewebsites.net
2. **SyncService**: Check https://terrafusionsyncservice.azurewebsites.net/health
3. **Application Insights**: Review metrics in the Azure Portal

## Azure Resources

The following Azure resources will be created:

| Resource | Type | Purpose |
|----------|------|---------|
| TerraFusionResourceGroup | Resource Group | Container for all resources |
| TerraFusionInsights | Application Insights | Monitoring and telemetry |
| TerraFusionPlan | App Service Plan | Hosting plan for web apps |
| TerraFusionGateway | Web App | API Gateway (Flask) |
| TerraFusionSyncService | Web App | SyncService (FastAPI) |
| terrafusion-db | PostgreSQL Server | Database server |
| terrafusiondb | PostgreSQL Database | Application database |

## Environment Variables

The following environment variables are configured automatically:

| Variable | Description |
|----------|-------------|
| DATABASE_URL | Connection string for the PostgreSQL database |
| APPINSIGHTS_INSTRUMENTATIONKEY | Instrumentation key for Application Insights |
| SESSION_SECRET | Secret key for session management |
| SYNC_SERVICE_URL | URL for the SyncService |
| API_GATEWAY_URL | URL for the API Gateway |

## Continuous Deployment

A GitHub Actions workflow is included for continuous deployment:

`.github/workflows/azure-deploy.yml`

To use it:
1. Store your publish profile as a GitHub secret named `AZURE_WEBAPP_PUBLISH_PROFILE`
2. Push changes to the main branch to trigger automatic deployment

## Monitoring

Azure Application Insights provides comprehensive monitoring:

1. **Performance Monitoring**: Track request durations, dependencies, and more
2. **Error Tracking**: Automatically capture and analyze exceptions
3. **Custom Events**: Track business-specific events
4. **Metrics**: Monitor system health and performance
5. **Alerts**: Set up notifications for critical issues

Access monitoring in the Azure Portal under the Application Insights resource.

## Troubleshooting

### Connection Issues
- Check that the database firewall rules allow connections from Azure services
- Verify that the connection strings in App Settings are correct

### Application Errors
- Review the Application Insights logs for exceptions
- Check the App Service logs in the Azure Portal
- Use the `/azure-health` endpoint to verify service health

### Deployment Failures
- Check the deployment logs in the Azure Portal
- Ensure that the publish profile is current
- Verify that all dependencies are in requirements.txt

## Maintenance

### Database Backups
Azure PostgreSQL automatically creates backups. To restore:
1. Go to the Azure Portal
2. Navigate to the PostgreSQL server
3. Select "Restore" and follow the prompts

### Scaling
To scale the application:
1. Go to the Azure Portal
2. Navigate to the App Service Plan
3. Adjust the pricing tier and instance count as needed