#!/bin/bash

# Deploy Coins for Change Platform using Helm with Bitnami charts
set -e

echo "🚀 Deploying Coins for Change Platform using Helm..."

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed or not in PATH"
    echo "Please install Helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

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

# Configuration
NAMESPACE="coins-for-change"
RELEASE_NAME="coins-for-change"
CHART_PATH="./helm/coins-for-change"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t coins-for-change:latest .

# Create namespace if it doesn't exist
echo "🔧 Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Add Bitnami Helm repository
echo "📚 Adding Bitnami Helm repository..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Update Helm dependencies
echo "📦 Updating Helm dependencies..."
cd $CHART_PATH
helm dependency update
cd - > /dev/null

# Deploy the application
echo "🚀 Deploying application with Helm..."
helm upgrade --install $RELEASE_NAME $CHART_PATH \
    --namespace $NAMESPACE \
    --create-namespace \
    --wait \
    --timeout 10m \
    --set image.tag=latest \
    --set image.pullPolicy=Never \
    --set postgresql.auth.postgresPassword=postgres123 \
    --set app.environment=development \
    --set app.debug=true

echo "✅ Deployment completed successfully!"

# Show deployment status
echo ""
echo "📊 Deployment Status:"
helm status $RELEASE_NAME -n $NAMESPACE
echo ""
kubectl get all -n $NAMESPACE

echo ""
echo "🔗 Access the application:"
echo "Port forward to access locally:"
echo "kubectl port-forward service/$RELEASE_NAME 8000:80 -n $NAMESPACE"

echo ""
echo "🏥 Health check endpoints:"
echo "- Health: http://localhost:8000/health"
echo "- Ready: http://localhost:8000/ready"
echo "- Startup: http://localhost:8000/startup"

echo ""
echo "📝 View application logs:"
echo "kubectl logs -f deployment/$RELEASE_NAME -n $NAMESPACE"

echo ""
echo "🐘 Connect to PostgreSQL:"
echo "kubectl exec -it deployment/$RELEASE_NAME-postgresql -n $NAMESPACE -- psql -U postgres -d coins_for_change"

echo ""
echo "🔐 Get PostgreSQL password:"
echo "kubectl get secret $RELEASE_NAME-postgresql -n $NAMESPACE -o jsonpath='{.data.postgres-password}' | base64 -d"

echo ""
echo "📊 View Helm values:"
echo "helm get values $RELEASE_NAME -n $NAMESPACE"