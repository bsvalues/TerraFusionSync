#!/bin/bash
# GitOps synchronization script for TerraFusion SyncService Platform
# This script syncs Kubernetes manifests from a Git repository to the cluster

set -e

# Default values
GIT_REPO="https://github.com/example/terrafusion-gitops.git"
GIT_BRANCH="main"
SYNC_DIR="/tmp/terrafusion-gitops"
KUBE_CONTEXT="default"
ENVIRONMENT="prod"  # prod, stage, or dev
DRY_RUN="false"

# Print help message
function show_help {
    echo "GitOps Synchronization Script for TerraFusion SyncService Platform"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -r, --repo REPO             Git repository URL (default: $GIT_REPO)"
    echo "  -b, --branch BRANCH         Git branch (default: $GIT_BRANCH)"
    echo "  -d, --dir DIR               Local directory for sync (default: $SYNC_DIR)"
    echo "  -c, --context CONTEXT       Kubernetes context (default: $KUBE_CONTEXT)"
    echo "  -e, --environment ENV       Environment to sync (prod, stage, dev, default: $ENVIRONMENT)"
    echo "  --dry-run                   Don't apply changes, just show what would happen"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --environment stage"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -r|--repo)
            GIT_REPO="$2"
            shift 2
            ;;
        -b|--branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        -d|--dir)
            SYNC_DIR="$2"
            shift 2
            ;;
        -c|--context)
            KUBE_CONTEXT="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
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

# Validate environment
if [[ "$ENVIRONMENT" != "prod" && "$ENVIRONMENT" != "stage" && "$ENVIRONMENT" != "dev" ]]; then
    echo "Error: Environment must be one of: prod, stage, dev"
    exit 1
fi

echo "=== TerraFusion GitOps Synchronization ==="
echo "Git Repository: $GIT_REPO"
echo "Git Branch: $GIT_BRANCH"
echo "Sync Directory: $SYNC_DIR"
echo "Kubernetes Context: $KUBE_CONTEXT"
echo "Environment: $ENVIRONMENT"
echo "Dry Run: $DRY_RUN"
echo "============================================"

# Create temp directory if it doesn't exist
if [[ -d "$SYNC_DIR" ]]; then
    echo "Cleaning existing sync directory..."
    rm -rf "$SYNC_DIR"
fi

echo "Creating sync directory..."
mkdir -p "$SYNC_DIR"

# Clone Git repository
echo "Cloning Git repository..."
git clone -b "$GIT_BRANCH" "$GIT_REPO" "$SYNC_DIR"

# Change to repository directory
cd "$SYNC_DIR"

# Set Kubernetes context
echo "Setting Kubernetes context to $KUBE_CONTEXT..."
kubectl config use-context "$KUBE_CONTEXT"

# Get the current cluster state
echo "Getting current cluster state..."
NAMESPACE="terrafusion-$ENVIRONMENT"
mkdir -p "$SYNC_DIR/current-state"
kubectl get -n "$NAMESPACE" deployments,services,ingress,configmaps -o yaml > "$SYNC_DIR/current-state/current-state.yaml"

# Build kustomize for the specified environment
echo "Building kustomize for $ENVIRONMENT environment..."
KUSTOMIZE_DIR="$SYNC_DIR/kubernetes/overlays/$ENVIRONMENT"
if [[ ! -d "$KUSTOMIZE_DIR" ]]; then
    echo "Error: Kustomize directory for $ENVIRONMENT not found at $KUSTOMIZE_DIR"
    exit 1
fi

# Apply or show changes
if [[ "$DRY_RUN" == "true" ]]; then
    echo "Dry run: Showing what would be applied..."
    kubectl kustomize "$KUSTOMIZE_DIR"
    echo "Dry run: Showing diff..."
    kubectl diff -k "$KUSTOMIZE_DIR"
else
    echo "Applying kustomize to cluster..."
    kubectl apply -k "$KUSTOMIZE_DIR"

    # Wait for deployments to be ready
    echo "Waiting for deployments to be ready..."
    DEPLOYMENTS=$(kubectl get deployments -n "$NAMESPACE" -o name)
    for DEPLOYMENT in $DEPLOYMENTS; do
        echo "Waiting for $DEPLOYMENT to be ready..."
        kubectl rollout status -n "$NAMESPACE" "$DEPLOYMENT" --timeout=300s
    done
fi

# Create GitOps summary
echo "Creating GitOps sync summary..."
SUMMARY_FILE="$SYNC_DIR/gitops-sync-summary.txt"
echo "GitOps Sync Summary" > "$SUMMARY_FILE"
echo "Date: $(date)" >> "$SUMMARY_FILE"
echo "Environment: $ENVIRONMENT" >> "$SUMMARY_FILE"
echo "Git Commit: $(git rev-parse HEAD)" >> "$SUMMARY_FILE"
echo "Resources:" >> "$SUMMARY_FILE"
kubectl get -n "$NAMESPACE" deployments,services,ingress,configmaps -o wide >> "$SUMMARY_FILE"

echo "GitOps synchronization complete!"
echo "Summary saved to $SUMMARY_FILE"
exit 0