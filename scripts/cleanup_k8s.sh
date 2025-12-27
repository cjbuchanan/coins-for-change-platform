#!/bin/bash

# Cleanup Coins for Change Platform from Kubernetes
set -e

echo "🧹 Cleaning up Coins for Change Platform from Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

echo "🗑️ Deleting application resources..."
kubectl delete -f k8s/app-service.yaml --ignore-not-found=true
kubectl delete -f k8s/app-deployment.yaml --ignore-not-found=true

echo "🗑️ Deleting migration job..."
kubectl delete -f k8s/migration-job.yaml --ignore-not-found=true

echo "🗑️ Deleting PostgreSQL resources..."
kubectl delete -f k8s/postgres-service.yaml --ignore-not-found=true
kubectl delete -f k8s/postgres-deployment.yaml --ignore-not-found=true

echo "🗑️ Deleting persistent volume claim..."
kubectl delete -f k8s/postgres-pvc.yaml --ignore-not-found=true

echo "🗑️ Deleting secrets and config maps..."
kubectl delete -f k8s/app-secret.yaml --ignore-not-found=true
kubectl delete -f k8s/app-configmap.yaml --ignore-not-found=true
kubectl delete -f k8s/postgres-configmap.yaml --ignore-not-found=true
kubectl delete -f k8s/postgres-secret.yaml --ignore-not-found=true

echo "🗑️ Deleting namespace..."
kubectl delete -f k8s/namespace.yaml --ignore-not-found=true

echo "🧹 Cleanup completed!"

# Show remaining resources (should be empty)
echo ""
echo "📊 Remaining resources in namespace:"
kubectl get all -n coins-for-change 2>/dev/null || echo "Namespace not found (expected)"