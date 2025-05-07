# TerraFusion CLI

A unified command-line tool for managing TerraFusion deployments and operations.

## Features

- **Unified Interface**: Single executable for all TerraFusion operations
- **Multi-Environment Support**: Manage dev, stage, and production environments
- **Deployment Operations**: Deploy, rollback, and check status
- **GitOps Integration**: Sync with GitOps repositories
- **Health Monitoring**: Check system health across components
- **Log Access**: View logs for all components
- **Build Support**: Build and push container images

## Installation

```bash
# Copy the executable to a location in your PATH
cp terraform_cli.py /usr/local/bin/terrafusion
chmod +x /usr/local/bin/terrafusion

# Verify installation
terrafusion --version
```

## Configuration

The CLI stores its configuration in `~/.terrafusion/config.json`. You can view and modify the configuration with:

```bash
# View current configuration
terrafusion config view

# Set a configuration value
terrafusion config set kube_context my-cluster

# Set a nested configuration value
terrafusion config set environments.prod.domain terrafusion.example.com
```

## Deployment Operations

### Deploy TerraFusion

```bash
# Deploy to development environment
terrafusion deploy -e dev

# Deploy specific component to staging
terrafusion deploy -e stage --component sync-service

# Deploy with specific version
terrafusion deploy -e prod --version v1.2.3

# Perform a dry run (show what would be deployed)
terrafusion deploy -e dev --dry-run

# Blue-green deployment (production only)
terrafusion deploy -e prod --blue-green
```

### Rollback Deployments

```bash
# Rollback most recent deployment in production
terrafusion rollback -e prod

# Rollback specific component
terrafusion rollback -e prod --component api-gateway

# Rollback to specific revision
terrafusion rollback -e prod --revision 2
```

### Check Status

```bash
# Check status in development environment
terrafusion status -e dev

# Get detailed status with events and resource usage
terrafusion status -e prod --detailed
```

## Health Monitoring

```bash
# Check health of all components
terrafusion health -e prod

# Check health of specific component
terrafusion health -e prod --component sync-service
```

## Log Access

```bash
# View recent logs for a component
terrafusion logs -e prod --component api-gateway

# View more lines
terrafusion logs -e prod --component sync-service --tail 500

# Follow logs in real-time
terrafusion logs -e dev --component api-gateway --follow
```

## GitOps Operations

```bash
# Sync from GitOps repository
terrafusion gitops sync -e prod

# Sync with alternative repository
terrafusion gitops sync -e stage --repo https://github.com/myorg/terrafusion-manifests.git

# Dry run to see what would change
terrafusion gitops sync -e prod --dry-run
```

## Build Operations

```bash
# Build all components
terrafusion build

# Build specific component
terrafusion build --component api-gateway

# Build with custom tag
terrafusion build --tag v1.2.3

# Build and push to registry
terrafusion build --tag v1.2.3 --push
```

## Example Workflow

```bash
# Initial deployment to development
terrafusion deploy -e dev

# Check status
terrafusion status -e dev

# View logs
terrafusion logs -e dev --component api-gateway

# If everything looks good, deploy to staging
terrafusion deploy -e stage

# Verify health
terrafusion health -e stage

# Deploy to production with blue-green strategy
terrafusion deploy -e prod --blue-green

# If issues occur, rollback
terrafusion rollback -e prod
```

## Requirements

- Python 3.6+
- kubectl
- kustomize
- git
- docker (for build operations)