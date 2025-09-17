# MCP Server Configuration Guide

This document provides comprehensive guidance for configuring and troubleshooting
MCP (Model Context Protocol) servers for the Coins for Change platform
development workflow.

## Overview

The platform uses multiple MCP servers to integrate with various development
tools and services:

- **PostgreSQL**: Database operations, schema management, and query execution
- **GitHub**: Repository management, issue tracking, and pull request operations
- **Kubernetes**: Cluster management, deployment operations, and resource
  monitoring
- **Prometheus**: Metrics querying, alerting rules, and performance monitoring
- **Redis**: Cache management, session storage, and real-time operations
- **Docker**: Container operations, image management, and local development
- **Testing (pytest)**: Test execution, coverage reporting, and quality assurance
- **Confluence**: Knowledge management and API documentation (optional)
- **Vault**: Secrets management and credential storage (optional)

## Prerequisites

### Install uv and uvx

The MCP servers use `uvx` (part of the `uv` Python package manager) to run.
Install it first:

**macOS (using Homebrew):**

```bash
brew install uv
```

**Alternative installation methods:**

```bash
# Using pip
pip install uv

# Using pipx
pipx install uv

# Direct installation (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify installation:**

```bash
uv --version
uvx --version
```

## Server Configuration Details

### PostgreSQL MCP Server

**Purpose**: Database operations, schema management, and query execution

**Configuration:**

```json
{
  "postgresql": {
    "command": "uvx",
    "args": ["mcp-server-postgres@latest"],
    "env": {
      "POSTGRES_CONNECTION_STRING": "postgresql://localhost:5432/coins_for_change",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "postgres_query",
      "postgres_schema_info", 
      "postgres_list_tables"
    ]
  }
}
```

**Setup Requirements:**

1. PostgreSQL server running locally or accessible remotely
2. Database `coins_for_change` created
3. Connection string updated with correct credentials

**Environment Variables:**

- `POSTGRES_CONNECTION_STRING`: Full PostgreSQL connection string
- `FASTMCP_LOG_LEVEL`: Logging level (ERROR, WARN, INFO, DEBUG)

### GitHub MCP Server

**Purpose**: Repository management, issue tracking, and pull request operations

**Configuration:**

```json
{
  "github": {
    "command": "uvx", 
    "args": ["mcp-server-github@latest"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "github_list_repositories",
      "github_get_repository", 
      "github_list_issues"
    ]
  }
}
```

**Setup Requirements:**

1. GitHub Personal Access Token with appropriate permissions:
   - `repo` (for repository access)
   - `issues` (for issue management)
   - `pull_requests` (for PR operations)

**To create a GitHub token:**

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select required scopes
4. Copy token and add to environment variable

### Kubernetes MCP Server

**Purpose**: Cluster management, deployment operations, and resource monitoring

**Configuration:**

```json
{
  "kubernetes": {
    "command": "uvx",
    "args": ["mcp-server-kubernetes@latest"], 
    "env": {
      "KUBECONFIG": "~/.kube/config",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "kubectl_get_pods",
      "kubectl_get_services",
      "kubectl_get_deployments",
      "kubectl_describe"
    ]
  }
}
```

**Setup Requirements:**

1. kubectl installed and configured
2. Valid kubeconfig file at `~/.kube/config`
3. Access to target Kubernetes cluster

### Prometheus MCP Server

**Purpose**: Metrics querying, alerting rules, and performance monitoring

**Configuration:**

```json
{
  "prometheus": {
    "command": "uvx",
    "args": ["mcp-server-prometheus@latest"],
    "env": {
      "PROMETHEUS_URL": "http://localhost:9090", 
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "prometheus_query",
      "prometheus_query_range",
      "prometheus_list_metrics"
    ]
  }
}
```

**Setup Requirements:**

1. Prometheus server running and accessible
2. Update `PROMETHEUS_URL` with correct endpoint

### Redis MCP Server

**Purpose**: Cache management, session storage, and real-time operations

**Configuration:**

```json
{
  "redis": {
    "command": "uvx",
    "args": ["mcp-server-redis@latest"],
    "env": {
      "REDIS_URL": "redis://localhost:6379",
      "FASTMCP_LOG_LEVEL": "ERROR" 
    },
    "disabled": false,
    "autoApprove": [
      "redis_get",
      "redis_set", 
      "redis_keys",
      "redis_info"
    ]
  }
}
```

**Setup Requirements:**

1. Redis server running locally or accessible remotely
2. Update `REDIS_URL` with correct connection details

### Docker MCP Server

**Purpose**: Container operations, image management, and local development

**Configuration:**

```json
{
  "docker": {
    "command": "uvx",
    "args": ["mcp-server-docker@latest"],
    "env": {
      "DOCKER_HOST": "unix:///var/run/docker.sock",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "docker_list_containers",
      "docker_list_images",
      "docker_inspect", 
      "docker_logs"
    ]
  }
}
```

**Setup Requirements:**

1. Docker daemon running
2. User has permissions to access Docker socket
3. On macOS/Windows: Docker Desktop installed and running

### Testing (pytest) MCP Server

**Purpose**: Test execution, coverage reporting, and quality assurance

**Configuration:**

```json
{
  "testing": {
    "command": "uvx",
    "args": ["mcp-server-pytest@latest"],
    "env": {
      "PYTEST_CONFIG": "pyproject.toml",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": [
      "pytest_run_tests",
      "pytest_collect_tests",
      "pytest_coverage_report"
    ]
  }
}
```

**Setup Requirements:**

1. Python project with pytest configuration
2. `pyproject.toml` or `pytest.ini` configuration file

### Confluence MCP Server (Optional)

**Purpose**: Knowledge management and API documentation

**Configuration:**

```json
{
  "confluence": {
    "command": "uvx",
    "args": ["mcp-server-confluence@latest"],
    "env": {
      "CONFLUENCE_URL": "",
      "CONFLUENCE_USERNAME": "",
      "CONFLUENCE_API_TOKEN": "",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": true,
    "autoApprove": [
      "confluence_search",
      "confluence_get_page",
      "confluence_create_page"
    ]
  }
}
```

**Setup Requirements:**

1. Confluence instance (Cloud or Server)
2. API token for authentication
3. Update environment variables with correct values

### Vault MCP Server (Optional)

**Purpose**: Secrets management and credential storage

**Configuration:**

```json
{
  "vault": {
    "command": "uvx", 
    "args": ["mcp-server-vault@latest"],
    "env": {
      "VAULT_ADDR": "http://localhost:8200",
      "VAULT_TOKEN": "",
      "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": true,
    "autoApprove": [
      "vault_read_secret",
      "vault_list_secrets"
    ]
  }
}
```

**Setup Requirements:**

1. HashiCorp Vault server running
2. Valid Vault token with appropriate permissions
3. Update `VAULT_ADDR` and `VAULT_TOKEN`

## Testing MCP Server Connections

### Basic Connection Test

Use Kiro's MCP testing capabilities to verify server connections:

1. Open Kiro command palette (Cmd/Ctrl + Shift + P)
2. Search for "MCP: Test Server Connection"
3. Select each server to test connectivity

### Manual Testing Commands

You can also test servers manually using uvx:

```bash
# Test PostgreSQL server
uvx mcp-server-postgres@latest --help

# Test GitHub server  
uvx mcp-server-github@latest --help

# Test Kubernetes server
uvx mcp-server-kubernetes@latest --help
```

### Sample Operations

Test each server with sample operations:

**PostgreSQL:**

```sql
-- Test query
SELECT version();
SELECT current_database();
```

**GitHub:**

```bash
# List repositories (via MCP)
# This would be done through Kiro's MCP interface
```

**Kubernetes:**

```bash
# Get pods
kubectl get pods --all-namespaces

# Get services
kubectl get services
```

**Redis:**

```bash
# Test connection
redis-cli ping

# Get info
redis-cli info
```

**Docker:**

```bash
# List containers
docker ps

# List images
docker images
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. uvx Command Not Found

**Problem**: `uvx: command not found`

**Solution:**

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using homebrew on macOS
brew install uv

# Restart terminal or source profile
source ~/.bashrc  # or ~/.zshrc
```

#### 2. MCP Server Connection Failures

**Problem**: Server fails to connect or start

**Solutions:**

1. Check if the underlying service is running (PostgreSQL, Redis, etc.)
2. Verify environment variables are correctly set
3. Check network connectivity to remote services
4. Review server logs for specific error messages

#### 3. Permission Denied Errors

**Problem**: Docker socket permission denied

**Solution:**

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER

# Restart terminal or log out/in
```

**Problem**: Kubernetes access denied

**Solution:**

```bash
# Check kubeconfig
kubectl config current-context

# Verify cluster access
kubectl cluster-info
```

#### 4. Authentication Failures

**Problem**: GitHub API authentication fails

**Solution:**

1. Verify Personal Access Token is valid
2. Check token permissions/scopes
3. Ensure token hasn't expired

**Problem**: Database connection fails

**Solution:**

1. Check connection string format
2. Verify database exists
3. Test credentials manually:

```bash
psql "postgresql://user:pass@localhost:5432/coins_for_change"
```

#### 5. Server-Specific Issues

**PostgreSQL:**

- Ensure database server is running: `pg_ctl status`
- Check connection limits: `SHOW max_connections;`
- Verify user permissions

**Redis:**

- Check if Redis is running: `redis-cli ping`
- Verify Redis configuration
- Check memory usage

**Kubernetes:**

- Verify kubectl works: `kubectl version`
- Check cluster connectivity: `kubectl cluster-info`
- Validate RBAC permissions

### Debugging Steps

1. **Enable Debug Logging:**

   ```json
   {
     "env": {
       "FASTMCP_LOG_LEVEL": "DEBUG"
     }
   }
   ```

2. **Check Server Status:**
   - Use Kiro's MCP Server view in the feature panel
   - Look for connection status indicators
   - Review error messages

3. **Test Individual Components:**
   - Test underlying services independently
   - Verify credentials and permissions
   - Check network connectivity

4. **Review Configuration:**
   - Validate JSON syntax in mcp.json
   - Check environment variable values
   - Ensure server names are unique

### Getting Help

1. **Kiro Documentation**: Check Kiro's MCP documentation
2. **Server Documentation**: Review individual MCP server documentation
3. **Community Support**: Reach out to Kiro community forums
4. **Issue Tracking**: Report bugs to relevant repositories

## Configuration Management

### Environment-Specific Configurations

For different environments (development, staging, production), you can:

1. **Use Environment Variables:**

   ```bash
   export POSTGRES_CONNECTION_STRING="postgresql://prod-host:5432/coins_for_change"
   ```

2. **Multiple Configuration Files:**
   - `.kiro/settings/mcp.json` (workspace-level)
   - `~/.kiro/settings/mcp.json` (user-level)

3. **Conditional Enabling:**

   ```json
   {
     "disabled": true  // Disable in certain environments
   }
   ```

### Security Considerations

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Rotate tokens and credentials** regularly
4. **Limit permissions** to minimum required
5. **Monitor access logs** for unusual activity

### Maintenance

1. **Regular Updates:**

   ```bash
   # Update all MCP servers
   uvx --upgrade mcp-server-postgres@latest
   uvx --upgrade mcp-server-github@latest
   # ... etc
   ```

2. **Health Monitoring:**
   - Set up alerts for server failures
   - Monitor resource usage
   - Track connection success rates

3. **Backup Configurations:**
   - Version control MCP configurations
   - Document environment-specific settings
   - Maintain rollback procedures

## Best Practices

1. **Start with Essential Servers**: Enable core servers first (PostgreSQL,
   GitHub, Docker)
2. **Test Incrementally**: Add and test one server at a time
3. **Use Auto-Approve Carefully**: Only auto-approve safe, read-only operations
4. **Monitor Performance**: Watch for servers that slow down operations
5. **Keep Documentation Updated**: Update this guide as configurations change
6. **Regular Maintenance**: Update servers and review configurations periodically

This configuration provides a comprehensive development workflow integration that
supports database operations, version control, containerization, monitoring,
and testing - all essential components for the Coins for Change platform
development.
