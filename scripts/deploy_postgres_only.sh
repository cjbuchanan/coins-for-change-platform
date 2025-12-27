#!/bin/bash

# Deploy only PostgreSQL to Kubernetes for testing
set -e

echo "🐘 Deploying PostgreSQL to Kubernetes for database testing..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Apply Kubernetes manifests in order
echo "🔧 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "🔐 Creating secrets and config maps..."
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml

echo "💾 Creating persistent volume claim..."
kubectl apply -f k8s/postgres-pvc.yaml

echo "🐘 Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n coins-for-change

# Check if PostgreSQL is actually ready
echo "🔍 Checking PostgreSQL readiness..."
kubectl wait --for=condition=ready pod -l app=postgres -n coins-for-change --timeout=300s

echo "✅ PostgreSQL deployment completed successfully!"

# Show deployment status
echo ""
echo "📊 PostgreSQL Status:"
kubectl get all -n coins-for-change

echo ""
echo "🔗 Connect to PostgreSQL:"
echo "kubectl exec -it deployment/postgres -n coins-for-change -- psql -U postgres -d coins_for_change"

echo ""
echo "🔌 Port forward to access locally:"
echo "kubectl port-forward service/postgres 5432:5432 -n coins-for-change"

echo ""
echo "📝 View PostgreSQL logs:"
echo "kubectl logs -f deployment/postgres -n coins-for-change"