# Technology Stack

This document defines the standard technology stack for this project, prioritizing CNCF graduated projects for ecosystem alignment and long-term stability.

## Infrastructure (CNCF Graduated)
- **Container Orchestration**: Kubernetes
- **Container Runtime**: containerd
- **Service Mesh**: Envoy Proxy (via Istio or standalone)
- **Ingress Controller**: Envoy-based (recommended) or NGINX Ingress Controller
- **Deployment**: Containerized applications on Kubernetes clusters

## Backend
- **Primary Language**: Python
- **Web Framework**: FastAPI
- **Databases**: 
  - **Search Engine**: OpenSearch (for full-text search, analytics, and document storage)
  - **Relational Database**: PostgreSQL (for structured data and transactions)
  - **Cache**: Redis or Valkey

## Architecture Principles
- Use FastAPI for all API endpoints with automatic OpenAPI documentation
- Leverage async/await patterns for database and search operations
- Implement proper separation between PostgreSQL (structured data) and OpenSearch (search/analytics)
- Design services to be Kubernetes-native with proper health checks and resource management
- Use SQLAlchemy for PostgreSQL ORM with async support
- Use opensearch-py client for OpenSearch operations
- Prefer CNCF graduated projects for infrastructure components

## Observability (CNCF Graduated)
- **Telemetry Standard**: OpenTelemetry for all observability data
- **Distributed Tracing**: Jaeger (CNCF graduated) for trace collection and analysis
- **Metrics**: Prometheus (CNCF graduated) for metrics collection and storage
- **Logging**: Fluentd (CNCF graduated) for log aggregation with OpenTelemetry correlation IDs
- **Monitoring**: Grafana for visualization and alerting
- **Service Mesh Observability**: Envoy Proxy metrics and tracing integration

## Development Guidelines
- All new services should follow FastAPI patterns and conventions
- Use Pydantic models for request/response validation
- Implement proper error handling and logging with OpenTelemetry instrumentation
- Design APIs to be RESTful where appropriate
- Use dependency injection for database connections and external services
- Instrument all services with OpenTelemetry for tracing, metrics, and logging
- Include correlation IDs in all log messages and API responses
- Implement health check endpoints for Kubernetes probes

## Additional Guidance
For comprehensive development guidance, refer to these additional steering documents:
- **coding-standards.md**: Detailed coding standards, patterns, and best practices
- **business-rules.md**: Core business rules and domain logic requirements  
- **api-design-standards.md**: RESTful API design conventions and standards
- **development-workflow.md**: Git workflow, testing strategy, and quality assurance
- **deployment-guide.md**: Infrastructure setup, deployment, and operational procedures

These documents work together to provide complete guidance for developing, testing, and deploying the Coins for Change platform.