#!/bin/bash
# Blue-Green Deployment script for TerraFusion SyncService Platform
# This script implements a blue-green deployment strategy using Kubernetes

set -e

# Default values
NAMESPACE="terrafusion-prod"
VERSION="latest"
COMPONENT="all"
DEPLOY_TIMEOUT="300s"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBE_CMD="kubectl"

# Print help message
function show_help {
    echo "Blue-Green Deployment Script for TerraFusion SyncService Platform"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE   Kubernetes namespace (default: terrafusion-prod)"
    echo "  -v, --version VERSION       Docker image version/tag (default: latest)"
    echo "  -c, --component COMPONENT   Component to deploy: api-gateway, sync-service, websocket, all (default: all)"
    echo "  -t, --timeout TIMEOUT       Deployment timeout (default: 300s)"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --namespace terrafusion-prod --version v1.2.3 --component api-gateway"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -t|--timeout)
            DEPLOY_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "=== TerraFusion Blue-Green Deployment ==="
echo "Namespace: $NAMESPACE"
echo "Version: $VERSION"
echo "Component: $COMPONENT"
echo "Timeout: $DEPLOY_TIMEOUT"
echo "========================================"

# Validate namespace
if ! $KUBE_CMD get namespace "$NAMESPACE" &> /dev/null; then
    echo "Error: Namespace $NAMESPACE does not exist"
    exit 1
fi

# Deploy to staging first
STAGE_NAMESPACE="${NAMESPACE/prod/stage}"
if ! $KUBE_CMD get namespace "$STAGE_NAMESPACE" &> /dev/null; then
    echo "Error: Staging namespace $STAGE_NAMESPACE does not exist"
    exit 1
fi

echo "Deploying to staging environment ($STAGE_NAMESPACE)..."

# Deploy to staging based on component
if [[ "$COMPONENT" == "all" || "$COMPONENT" == "api-gateway" ]]; then
    echo "Updating api-gateway image in staging..."
    $KUBE_CMD set image deployment/stage-api-gateway api-gateway=terrafusion/api-gateway:$VERSION -n $STAGE_NAMESPACE
    echo "Waiting for api-gateway rollout to complete in staging..."
    $KUBE_CMD rollout status deployment/stage-api-gateway -n $STAGE_NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "sync-service" ]]; then
    echo "Updating sync-service image in staging..."
    $KUBE_CMD set image deployment/stage-sync-service sync-service=terrafusion/sync-service:$VERSION -n $STAGE_NAMESPACE
    echo "Waiting for sync-service rollout to complete in staging..."
    $KUBE_CMD rollout status deployment/stage-sync-service -n $STAGE_NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "websocket" ]]; then
    echo "Updating websocket-server image in staging..."
    $KUBE_CMD set image deployment/stage-websocket-server websocket-server=terrafusion/websocket-server:$VERSION -n $STAGE_NAMESPACE
    echo "Waiting for websocket-server rollout to complete in staging..."
    $KUBE_CMD rollout status deployment/stage-websocket-server -n $STAGE_NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

echo "Staging deployment complete. Verifying staging environment..."

# Verify staging deployment
STAGING_URL="https://stage.terrafusion.example.com"
MAX_RETRIES=10
RETRY_DELAY=5

echo "Verifying staging endpoint at $STAGING_URL..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s --fail "$STAGING_URL/api/status" > /dev/null; then
        echo "Staging verification successful!"
        break
    fi
    
    if [[ $i -eq $MAX_RETRIES ]]; then
        echo "Error: Failed to verify staging deployment after $MAX_RETRIES attempts"
        echo "Please check the staging environment manually before proceeding to production"
        exit 1
    fi
    
    echo "Attempt $i failed, retrying in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done

# Prompt for confirmation before deploying to production
read -p "Do you want to proceed with the production deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Production deployment aborted"
    exit 0
fi

echo "Deploying to production environment ($NAMESPACE)..."

# Deploy to production based on component
if [[ "$COMPONENT" == "all" || "$COMPONENT" == "api-gateway" ]]; then
    echo "Updating api-gateway image in production..."
    $KUBE_CMD set image deployment/prod-api-gateway api-gateway=terrafusion/api-gateway:$VERSION -n $NAMESPACE
    echo "Waiting for api-gateway rollout to complete in production..."
    $KUBE_CMD rollout status deployment/prod-api-gateway -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "sync-service" ]]; then
    echo "Updating sync-service image in production..."
    $KUBE_CMD set image deployment/prod-sync-service sync-service=terrafusion/sync-service:$VERSION -n $NAMESPACE
    echo "Waiting for sync-service rollout to complete in production..."
    $KUBE_CMD rollout status deployment/prod-sync-service -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "websocket" ]]; then
    echo "Updating websocket-server image in production..."
    $KUBE_CMD set image deployment/prod-websocket-server websocket-server=terrafusion/websocket-server:$VERSION -n $NAMESPACE
    echo "Waiting for websocket-server rollout to complete in production..."
    $KUBE_CMD rollout status deployment/prod-websocket-server -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

echo "Production deployment complete!"
echo "============================="
echo "Blue-Green deployment successful!"
echo "New version $VERSION is now active in production."
exit 0