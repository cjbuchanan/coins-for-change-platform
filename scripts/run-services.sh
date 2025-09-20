#!/bin/bash

# Script to run all microservices for development

set -e

echo "🚀 Starting Coins for Change Platform services..."

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_path="src.services.${service_name}.main:app"
    
    echo "🔧 Starting ${service_name} service on port ${port}..."
    poetry run uvicorn ${service_path} --reload --port ${port} --host 0.0.0.0 &
    
    # Store the PID
    echo $! > "/tmp/cfc-${service_name}.pid"
}

# Function to stop all services
stop_services() {
    echo "🛑 Stopping all services..."
    
    for service in auth campaigns ideas coins search notifications analytics; do
        if [ -f "/tmp/cfc-${service}.pid" ]; then
            pid=$(cat "/tmp/cfc-${service}.pid")
            if kill -0 $pid 2>/dev/null; then
                echo "   Stopping ${service} service (PID: ${pid})"
                kill $pid
            fi
            rm -f "/tmp/cfc-${service}.pid"
        fi
    done
    
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap stop_services SIGINT SIGTERM

# Start all services
start_service "auth" 8001
start_service "campaigns" 8002
start_service "ideas" 8003
start_service "coins" 8004
start_service "search" 8005
start_service "notifications" 8006
start_service "analytics" 8007

echo ""
echo "✅ All services started!"
echo ""
echo "📚 API Documentation available at:"
echo "   - Auth Service: http://localhost:8001/docs"
echo "   - Campaign Service: http://localhost:8002/docs"
echo "   - Ideas Service: http://localhost:8003/docs"
echo "   - Coins Service: http://localhost:8004/docs"
echo "   - Search Service: http://localhost:8005/docs"
echo "   - Notifications Service: http://localhost:8006/docs"
echo "   - Analytics Service: http://localhost:8007/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait