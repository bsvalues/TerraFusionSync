# TerraFusion SyncService Platform Deployment Guide

This directory contains Kubernetes deployment configurations for the TerraFusion SyncService Platform, supporting a blue-green deployment strategy for zero-downtime deployments.

## Architecture Overview

The deployment architecture consists of:

1. **Base Configuration**: Common resources used across all environments
2. **Environment Overlays**: Environment-specific configurations for dev, stage, and prod
3. **Blue-Green Deployment**: A strategy for zero-downtime deployments using staging as a blue environment

## Directory Structure

```
kubernetes/
├── base/                   # Base Kubernetes resources
│   ├── api-gateway-deployment.yaml
│   ├── sync-service-deployment.yaml
│   ├── websocket-deployment.yaml
│   ├── database-deployment.yaml
│   ├── ingress.yaml
│   ├── prometheus-servicemonitor.yaml
│   └── kustomization.yaml
│
├── overlays/               # Environment-specific overlays
│   ├── dev/                # Development environment
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── ...
│   │
│   ├── stage/              # Staging environment (Blue)
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── api-gateway-patch.yaml
│   │   ├── sync-service-patch.yaml
│   │   ├── ingress-patch.yaml
│   │   └── ...
│   │
│   └── prod/               # Production environment (Green)
│       ├── kustomization.yaml
│       ├── namespace.yaml
│       ├── api-gateway-patch.yaml
│       ├── sync-service-patch.yaml
│       ├── ingress-patch.yaml
│       ├── autoscaling.yaml
│       ├── network-policies.yaml
│       ├── pod-disruption-budgets.yaml
│       ├── persistent-volumes.yaml
│       └── ...
```

## Deployment Features

The TerraFusion deployment infrastructure includes:

1. **Multi-Environment Support**: Separate configurations for dev, stage, and prod environments
2. **Blue-Green Deployment**: Zero-downtime deployments by promoting stage to prod
3. **Autoscaling**: Horizontal Pod Autoscalers for dynamic scaling
4. **Network Policies**: Secure network communication between components
5. **Pod Disruption Budgets**: Maintain availability during cluster maintenance
6. **Persistent Volumes**: Durable storage for logs and data
7. **Prometheus Monitoring**: Built-in monitoring integration
8. **GitOps Workflow**: Automated deployment process

## Deployment Process

### Manual Deployment

For manual deployment, use:

```bash
# Deploy to development environment
kubectl apply -k kubernetes/overlays/dev

# Deploy to staging environment
kubectl apply -k kubernetes/overlays/stage

# Deploy to production environment
kubectl apply -k kubernetes/overlays/prod
```

### Blue-Green Deployment

For blue-green deployments, use the provided scripts:

```bash
# Deploy a new version to staging (Blue)
./scripts/blue-green-deploy.sh --namespace terrafusion-prod --version v1.2.3

# The script will automatically:
# 1. Deploy to staging environment
# 2. Verify functionality
# 3. Prompt for confirmation
# 4. Deploy to production environment
```

### GitOps Deployment

For GitOps-based deployments:

1. Changes to Kubernetes manifests in the `main` branch trigger the GitOps workflow
2. The workflow validates the manifests
3. Deploys to the specified environment
4. Verifies the deployment success

You can also manually trigger a deployment through the GitHub Actions UI.

### Rollback Process

If a deployment fails, use the rollback script:

```bash
# Rollback the production deployment
./scripts/rollback-deployment.sh --namespace terrafusion-prod

# Rollback to a specific revision
./scripts/rollback-deployment.sh --namespace terrafusion-prod --revision 3
```

## Monitoring and Observability

The deployment includes:

1. **Prometheus ServiceMonitors**: Automatic metrics collection
2. **Health Endpoints**: Integrated health checks for each component
3. **Logging**: Persistent log storage with volume mounts

## Security Considerations

The deployment implements:

1. **Network Policies**: Restrict communication between components
2. **Secure Secrets**: Managed through Kubernetes secrets with proper encryption
3. **TLS Termination**: Secure ingress with TLS certificates
4. **Pod Security Policies**: Enforce security best practices

## Prerequisites

- Kubernetes cluster (v1.22+)
- kubectl (v1.22+)
- kustomize (v4.5+)
- Access to container registries containing TerraFusion images
- Proper RBAC permissions to deploy to the target namespaces

## Adding New Components

When adding new components to the platform:

1. Add the base deployment in `kubernetes/base/`
2. Add environment-specific configurations in each overlay directory
3. Update the kustomization files to include the new resources
4. Update the blue-green deployment script to handle the new component

## Troubleshooting

Common issues and solutions:

1. **Pod startup failures**: Check events with `kubectl describe pod <pod-name>`
2. **Service connectivity issues**: Verify network policies and service selectors
3. **GitOps deployment failures**: Check GitHub Actions logs for details
4. **Resource constraints**: Adjust resource requests/limits in the component patches