#!/bin/bash

# Deploy Coins for Change Platform to Kubernetes
set -e

echo "🚀 Deploying Coins for Change Platform to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -t coins-for-change:latest .

# Apply Kubernetes manifests in order
echo "🔧 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "🔐 Creating secrets and config maps..."
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml
kubectl apply -f k8s/app-configmap.yaml
kubectl apply -f k8s/app-secret.yaml

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

echo "🔄 Running database migrations..."
kubectl apply -f k8s/migration-job.yaml

# Wait for migration job to complete
echo "⏳ Waiting for migration job to complete..."
kubectl wait --for=condition=complete job/database-migration -n coins-for-change --timeout=300s

echo "🚀 Deploying application..."
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/app-service.yaml

echo "⏳ Waiting for application to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/coins-for-change-app -n coins-for-change

echo "🔍 Checking application readiness..."
kubectl wait --for=condition=ready pod -l app=coins-for-change -n coins-for-change --timeout=300s

echo "✅ Deployment completed successfully!"

# Show deployment status
echo ""
echo "📊 Deployment Status:"
kubectl get all -n coins-for-change

echo ""
echo "🔗 Access the application:"
echo "Port forward to access locally:"
echo "kubectl port-forward service/coins-for-change-service 8000:80 -n coins-for-change"

echo ""
echo "🏥 Health check endpoints:"
echo "- Health: http://localhost:8000/health"
echo "- Ready: http://localhost:8000/ready"
echo "- Startup: http://localhost:8000/startup"

echo ""
echo "📝 View logs:"
echo "kubectl logs -f deployment/coins-for-change-app -n coins-for-change"

echo ""
echo "🐘 Connect to PostgreSQL:"
echo "kubectl exec -it deployment/postgres -n coins-for-change -- psql -U postgres -d coins_for_change"