#!/bin/bash

# Deploy PostgreSQL using Bitnami Helm chart
set -e

echo "🐘 Deploying PostgreSQL using Bitnami Helm chart..."

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed or not in PATH"
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Create namespace
echo "🔧 Creating namespace..."
kubectl create namespace coins-for-change --dry-run=client -o yaml | kubectl apply -f -

# Add Bitnami repository
echo "📦 Adding Bitnami Helm repository..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy PostgreSQL with custom values
echo "🚀 Deploying PostgreSQL..."
helm install postgres bitnami/postgresql \
  --namespace coins-for-change \
  --set auth.postgresPassword=postgres123 \
  --set auth.username=app_user \
  --set auth.password=app_password123 \
  --set auth.database=coins_for_change \
  --set primary.persistence.enabled=true \
  --set primary.persistence.size=5Gi \
  --set primary.resources.requests.memory=256Mi \
  --set primary.resources.requests.cpu=250m \
  --set primary.resources.limits.memory=512Mi \
  --set primary.resources.limits.cpu=500m \
  --set metrics.enabled=true \
  --set metrics.serviceMonitor.enabled=false \
  --wait --timeout=300s

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n coins-for-change --timeout=300s

echo "✅ PostgreSQL deployment completed successfully!"

# Show deployment status
echo ""
echo "📊 PostgreSQL Status:"
kubectl get all -l app.kubernetes.io/name=postgresql -n coins-for-change

echo ""
echo "🔐 PostgreSQL Connection Details:"
echo "Host: postgres-postgresql.coins-for-change.svc.cluster.local"
echo "Port: 5432"
echo "Database: coins_for_change"
echo "Username: app_user"
echo "Password: app_password123"
echo "Admin Username: postgres"
echo "Admin Password: postgres123"

echo ""
echo "🔗 Connection String:"
echo "postgresql+asyncpg://app_user:app_password123@postgres-postgresql.coins-for-change.svc.cluster.local:5432/coins_for_change"

echo ""
echo "🔌 Port forward to access locally:"
echo "kubectl port-forward service/postgres-postgresql 5432:5432 -n coins-for-change"

echo ""
echo "🐘 Connect to PostgreSQL:"
echo "kubectl exec -it deployment/postgres-postgresql -n coins-for-change -- psql -U app_user -d coins_for_change"

echo ""
echo "📝 View PostgreSQL logs:"
echo "kubectl logs -f deployment/postgres-postgresql -n coins-for-change"