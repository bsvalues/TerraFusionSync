#!/bin/bash
# Rollback script for TerraFusion SyncService Platform
# This script rolls back a deployment in case of issues

set -e

# Default values
NAMESPACE="terrafusion-prod"
COMPONENT="all"
REVISION="previous"  # "previous" or a specific revision number
DEPLOY_TIMEOUT="300s"
KUBE_CMD="kubectl"

# Print help message
function show_help {
    echo "Rollback Script for TerraFusion SyncService Platform"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE   Kubernetes namespace (default: terrafusion-prod)"
    echo "  -c, --component COMPONENT   Component to rollback: api-gateway, sync-service, websocket, all (default: all)"
    echo "  -r, --revision REVISION     Revision to rollback to ('previous' or a number, default: previous)"
    echo "  -t, --timeout TIMEOUT       Rollback timeout (default: 300s)"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --namespace terrafusion-prod --component api-gateway --revision 3"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -r|--revision)
            REVISION="$2"
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

echo "=== TerraFusion Deployment Rollback ==="
echo "Namespace: $NAMESPACE"
echo "Component: $COMPONENT"
echo "Revision: $REVISION"
echo "Timeout: $DEPLOY_TIMEOUT"
echo "========================================"

# Get the prefix for resources based on the namespace
PREFIX=""
if [[ "$NAMESPACE" == "terrafusion-prod" ]]; then
    PREFIX="prod-"
elif [[ "$NAMESPACE" == "terrafusion-stage" ]]; then
    PREFIX="stage-"
elif [[ "$NAMESPACE" == "terrafusion-dev" ]]; then
    PREFIX="dev-"
fi

# Check if namespace exists
if ! $KUBE_CMD get namespace "$NAMESPACE" &> /dev/null; then
    echo "Error: Namespace $NAMESPACE does not exist"
    exit 1
fi

# Rollback deployments based on component
if [[ "$COMPONENT" == "all" || "$COMPONENT" == "api-gateway" ]]; then
    DEPLOYMENT="${PREFIX}api-gateway"
    echo "Getting deployment history for $DEPLOYMENT..."
    $KUBE_CMD rollout history deployment/$DEPLOYMENT -n $NAMESPACE
    
    # If revision is "previous", don't specify it and let Kubernetes use the previous revision
    if [[ "$REVISION" == "previous" ]]; then
        echo "Rolling back $DEPLOYMENT to previous revision..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    else
        echo "Rolling back $DEPLOYMENT to revision $REVISION..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT --to-revision=$REVISION -n $NAMESPACE
    fi
    
    echo "Waiting for $DEPLOYMENT rollback to complete..."
    $KUBE_CMD rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "sync-service" ]]; then
    DEPLOYMENT="${PREFIX}sync-service"
    echo "Getting deployment history for $DEPLOYMENT..."
    $KUBE_CMD rollout history deployment/$DEPLOYMENT -n $NAMESPACE
    
    # If revision is "previous", don't specify it and let Kubernetes use the previous revision
    if [[ "$REVISION" == "previous" ]]; then
        echo "Rolling back $DEPLOYMENT to previous revision..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    else
        echo "Rolling back $DEPLOYMENT to revision $REVISION..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT --to-revision=$REVISION -n $NAMESPACE
    fi
    
    echo "Waiting for $DEPLOYMENT rollback to complete..."
    $KUBE_CMD rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

if [[ "$COMPONENT" == "all" || "$COMPONENT" == "websocket" ]]; then
    DEPLOYMENT="${PREFIX}websocket-server"
    echo "Getting deployment history for $DEPLOYMENT..."
    $KUBE_CMD rollout history deployment/$DEPLOYMENT -n $NAMESPACE
    
    # If revision is "previous", don't specify it and let Kubernetes use the previous revision
    if [[ "$REVISION" == "previous" ]]; then
        echo "Rolling back $DEPLOYMENT to previous revision..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    else
        echo "Rolling back $DEPLOYMENT to revision $REVISION..."
        $KUBE_CMD rollout undo deployment/$DEPLOYMENT --to-revision=$REVISION -n $NAMESPACE
    fi
    
    echo "Waiting for $DEPLOYMENT rollback to complete..."
    $KUBE_CMD rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=$DEPLOY_TIMEOUT
fi

echo "Verifying rollback..."
$KUBE_CMD get pods -n $NAMESPACE

echo "============================="
echo "Rollback complete!"
exit 0