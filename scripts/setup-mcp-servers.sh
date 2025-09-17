#!/bin/bash

# MCP Server Setup Script
# This script helps set up and configure MCP servers for the Coins for Change platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration file path
MCP_CONFIG=".kiro/settings/mcp.json"

echo -e "${BLUE}🔧 MCP Server Setup for Coins for Change Platform${NC}"
echo "=================================================="
echo

# Check if uv/uvx is installed
if ! command -v uvx &> /dev/null; then
    echo -e "${RED}❌ uvx is not installed${NC}"
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  # or using homebrew: brew install uv"
    exit 1
fi

echo -e "${GREEN}✅ uvx is available${NC}"
echo

# Function to check if a service is running
check_service() {
    local service=$1
    local command=$2
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✅ $service is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service is not running${NC}"
        return 1
    fi
}

# Function to enable/disable MCP server in config
toggle_server() {
    local server_name=$1
    local enable=$2
    
    if [ "$enable" = "true" ]; then
        echo -e "${BLUE}🔧 Enabling $server_name server...${NC}"
        # Use jq to update the disabled field
        if command -v jq &> /dev/null; then
            jq ".mcpServers.$server_name.disabled = false" "$MCP_CONFIG" > tmp.json && mv tmp.json "$MCP_CONFIG"
        else
            echo -e "${YELLOW}⚠️  jq not found, please manually set disabled: false for $server_name in $MCP_CONFIG${NC}"
        fi
    else
        echo -e "${BLUE}🔧 Disabling $server_name server...${NC}"
        if command -v jq &> /dev/null; then
            jq ".mcpServers.$server_name.disabled = true" "$MCP_CONFIG" > tmp.json && mv tmp.json "$MCP_CONFIG"
        else
            echo -e "${YELLOW}⚠️  jq not found, please manually set disabled: true for $server_name in $MCP_CONFIG${NC}"
        fi
    fi
}

# Check available services
echo "🔍 Checking available services..."
echo

# PostgreSQL
if check_service "PostgreSQL" "pg_isready -h localhost -p 5432"; then
    read -p "Enable PostgreSQL MCP server? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        toggle_server "postgresql" "true"
        echo "📝 Don't forget to update the POSTGRES_CONNECTION_STRING in $MCP_CONFIG"
    fi
fi

# Redis
if check_service "Redis" "redis-cli ping"; then
    read -p "Enable Redis MCP server? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        toggle_server "redis" "true"
    fi
fi

# Docker
if check_service "Docker" "docker version"; then
    read -p "Enable Docker MCP server? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        toggle_server "docker" "true"
    fi
fi

# GitHub (always ask since it requires token)
echo -e "${YELLOW}⚠️  GitHub MCP server requires a Personal Access Token${NC}"
read -p "Do you have a GitHub token and want to enable GitHub MCP server? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    toggle_server "github" "true"
    echo "📝 Please add your GitHub Personal Access Token to GITHUB_PERSONAL_ACCESS_TOKEN in $MCP_CONFIG"
    echo "   Create token at: https://github.com/settings/tokens"
    echo "   Required scopes: repo, issues, pull_requests"
fi

# Kubernetes
if [ -f ~/.kube/config ]; then
    if check_service "Kubernetes" "kubectl cluster-info"; then
        read -p "Enable Kubernetes MCP server? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            toggle_server "kubernetes" "true"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Kubernetes config not found at ~/.kube/config${NC}"
fi

# Filesystem server (always available)
read -p "Enable Filesystem MCP server for project access? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    toggle_server "filesystem" "true"
fi

# Shell server (always available but potentially dangerous)
echo -e "${YELLOW}⚠️  Shell MCP server allows command execution - use with caution${NC}"
read -p "Enable Shell MCP server? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    toggle_server "shell" "true"
fi

echo
echo "🎉 MCP server setup complete!"
echo
echo "Next steps:"
echo "1. Review the configuration in $MCP_CONFIG"
echo "2. Add any required credentials (GitHub token, database passwords, etc.)"
echo "3. Test the configuration: python3 scripts/test-mcp-servers.py"
echo "4. Restart Kiro to load the new MCP servers"
echo
echo "📚 For detailed configuration help, see: docs/mcp-server-configuration.md"