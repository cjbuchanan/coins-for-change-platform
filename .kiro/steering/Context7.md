---
inclusion: always
---

# Context7 Integration Guidelines

## Automatic Context7 Usage

Always use Context7 MCP tools for the following scenarios without explicit user requests:

### Code Generation and Implementation
- When implementing new features or services
- When creating database models, API endpoints, or business logic
- When setting up new components or modules
- When writing tests or configuration files

### Library and Framework Documentation
- Before using any external library or framework
- When implementing specific patterns (FastAPI, SQLAlchemy, Pydantic, etc.)
- When working with authentication, database operations, or API integrations
- When setting up monitoring, logging, or observability tools

### Configuration and Setup
- When configuring Kubernetes deployments or Docker containers
- When setting up CI/CD pipelines or infrastructure
- When implementing security patterns or authentication flows
- When configuring databases, caching, or search engines

## Context7 Workflow

1. **Resolve Library ID**: Use `mcp_context7_resolve_library_id` to find the correct library identifier
2. **Get Documentation**: Use `mcp_context7_get_library_docs` with appropriate topic focus
3. **Apply Best Practices**: Integrate documentation guidance with project coding standards

## Technology Stack Priorities

When using Context7, prioritize documentation for these technologies aligned with our stack:

### Backend Technologies
- **FastAPI**: API development, dependency injection, validation
- **SQLAlchemy**: Database models, async operations, migrations
- **Pydantic**: Data validation, serialization, type safety
- **PostgreSQL**: Database design, performance optimization
- **Redis/Valkey**: Caching strategies, session management
- **OpenSearch**: Search implementation, indexing strategies

### Infrastructure Technologies
- **Kubernetes**: Deployment patterns, resource management
- **Docker**: Container optimization, multi-stage builds
- **Prometheus**: Metrics collection, alerting rules
- **Grafana**: Dashboard creation, visualization
- **Jaeger**: Distributed tracing, performance monitoring

### Development Tools
- **pytest**: Testing patterns, fixtures, async testing
- **Alembic**: Database migrations, schema management
- **Black/isort**: Code formatting standards
- **mypy**: Type checking, static analysis

## Integration with Project Standards

When retrieving Context7 documentation:
- Focus on async/await patterns for Python code
- Emphasize CNCF graduated project alternatives
- Prioritize security best practices and input validation
- Include observability and monitoring considerations
- Align with RESTful API design standards

## Example Usage Scenarios

- **"Implement user authentication"** → Get FastAPI security docs + JWT handling
- **"Set up database models"** → Get SQLAlchemy async docs + migration patterns  
- **"Create API endpoints"** → Get FastAPI routing docs + validation patterns
- **"Deploy to Kubernetes"** → Get K8s deployment docs + best practices
- **"Add search functionality"** → Get OpenSearch docs + indexing strategies
