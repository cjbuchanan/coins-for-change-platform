# MCP Server Setup for Coins for Change Platform

This directory contains the MCP (Model Context Protocol) server configuration and setup tools for the Coins for Change platform development workflow.

## Quick Start

1. **Run the setup script:**
   ```bash
   ./scripts/setup-mcp-servers.sh
   ```

2. **Test the configuration:**
   ```bash
   python3 scripts/test-mcp-servers.py
   ```

3. **Review and customize:**
   - Edit `.kiro/settings/mcp.json` to adjust settings
   - Add credentials for services that require them
   - Enable/disable servers as needed

## Available MCP Servers

### Core Development Servers
- **PostgreSQL**: Database operations and schema management
- **Redis**: Cache management and session storage  
- **Docker**: Container operations and image management
- **Filesystem**: Project file access and management
- **Shell**: Command execution (use with caution)

### Integration Servers
- **GitHub**: Repository management and issue tracking
- **Kubernetes**: Cluster management and deployments
- **Prometheus**: Metrics querying and monitoring

### Testing Servers
- **Testing**: Python pytest integration
- **Confluence**: Documentation management (optional)
- **Vault**: Secrets management (optional)

## Configuration Files

- `.kiro/settings/mcp.json` - Main MCP server configuration
- `docs/mcp-server-configuration.md` - Detailed configuration guide
- `scripts/test-mcp-servers.py` - Configuration testing script
- `scripts/setup-mcp-servers.sh` - Interactive setup script

## Prerequisites

1. **Install uv/uvx:**
   ```bash
   # Using curl
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Using homebrew (macOS)
   brew install uv
   ```

2. **Install and start required services:**
   - PostgreSQL (for database operations)
   - Redis (for caching)
   - Docker (for container management)

3. **Set up credentials:**
   - GitHub Personal Access Token
   - Database connection strings
   - Service endpoints

## Security Notes

- All servers are disabled by default for security
- Only enable servers you actually need
- Be cautious with shell and filesystem access
- Store credentials securely (use environment variables)
- Review auto-approve lists carefully

## Troubleshooting

If you encounter issues:

1. Check the detailed troubleshooting guide in `docs/mcp-server-configuration.md`
2. Run the test script to identify specific problems
3. Verify that underlying services are running
4. Check credentials and permissions

## Support

For additional help:
- Review the comprehensive documentation in `docs/mcp-server-configuration.md`
- Check Kiro's MCP documentation
- Test individual servers using the test script