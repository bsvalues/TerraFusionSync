# TerraFusion Platform on Azure

This is an Azure-optimized version of the TerraFusion Platform, designed to run in environments where Docker and containerization are restricted, such as County networks.

## Quick Start

To quickly deploy the TerraFusion Platform to Azure, run the following command in PowerShell:

```powershell
./azure-quickstart.ps1
```

This script will guide you through the deployment process.

## Key Files

### Azure Infrastructure
- `azure-migration.ps1` - Creates all necessary Azure resources
- `azure-webapp-config.json` - Configuration for Azure Web Apps
- `deploy-to-azure.ps1` - Deploys the application code to Azure

### Application Code
- `app_azure.py` - Azure-ready version of the API Gateway
- `syncservice_azure.py` - Azure-ready version of the SyncService
- `app_insights_integration.py` - Application Insights integration module

### Documentation
- `AZURE_DEPLOYMENT.md` - Detailed deployment guide
- `README-AZURE.md` - This quick reference

## Monitoring with Application Insights

The Azure deployment includes comprehensive monitoring via Azure Application Insights:

- Request tracking
- Exception logging
- Performance metrics
- Custom events
- Distributed tracing

All monitoring is configured automatically during deployment.

## Advantages Over Docker

This Azure-based deployment offers several advantages in environments with Docker restrictions:

1. **No Local Containers** - Everything runs in Azure's managed services
2. **Simplified Deployment** - Automated scripts handle resource creation and deployment
3. **Integrated Monitoring** - Built-in Application Insights eliminates the need for Prometheus/Grafana
4. **Managed Database** - Azure PostgreSQL provides automatic backups and scaling
5. **Scalability** - Easily scale up or out as needed
6. **Security** - Azure's built-in security features and compliance certifications

## Directory Structure

```
├── .github/workflows/
│   └── azure-deploy.yml         # GitHub Actions workflow for CI/CD
├── app_azure.py                 # Azure version of the API Gateway
├── syncservice_azure.py         # Azure version of the SyncService
├── app_insights_integration.py  # Application Insights integration
├── azure-migration.ps1          # Azure infrastructure setup
├── azure-quickstart.ps1         # Quick start deployment script
├── azure-webapp-config.json     # Web App configuration
├── deploy-to-azure.ps1          # Deployment script
├── requirements.azure.txt       # Azure-specific dependencies
├── startup.sh                   # Azure Web App startup script
├── AZURE_DEPLOYMENT.md          # Detailed documentation
└── README-AZURE.md              # This file
```

## Next Steps

1. Review the full documentation in `AZURE_DEPLOYMENT.md`
2. Customize the deployment settings in `azure-webapp-config.json`
3. Deploy using `azure-quickstart.ps1`
4. Set up CI/CD using the provided GitHub Actions workflow

## Support

For assistance with Azure deployment, refer to the detailed documentation or contact the TerraFusion Platform team.