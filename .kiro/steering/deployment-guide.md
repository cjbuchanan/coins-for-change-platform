# Deployment and Operations Guide

This document provides comprehensive guidance for deploying, operating, and maintaining the Coins for Change platform.

## Infrastructure Overview

### Architecture Components (CNCF-Aligned)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Envoy Proxy   │    │   Web Frontend  │
│   (Ingress)     │────│  (API Gateway)  │────│   (React/Vue)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ Auth Service │ │Campaign Svc │ │ Idea Svc   │
        │              │ │             │ │            │
        └──────────────┘ └─────────────┘ └────────────┘
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ Coin Service │ │Search Svc   │ │Notification│
        │              │ │             │ │ Service    │
        └──────────────┘ └─────────────┘ └────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │  PostgreSQL  │ │ OpenSearch  │ │Redis/Valkey│
        │   (Primary)  │ │  (Search)   │ │  (Cache)   │
        └──────────────┘ └─────────────┘ └────────────┘
```

### Technology Stack Deployment (CNCF Graduated Projects Preferred)
- **Container Platform**: Kubernetes (CNCF graduated)
- **Container Runtime**: containerd (CNCF graduated)
- **Service Proxy**: Envoy Proxy (CNCF graduated) via Istio or standalone
- **Container Registry**: Harbor (CNCF graduated) or cloud alternatives
- **Database**: PostgreSQL (recommended for simplicity)
  - *Enterprise Alternative*: Vitess (CNCF graduated) for massive scale requirements
- **Search Engine**: OpenSearch (managed or self-hosted)
- **Cache**: Redis/Valkey (recommended for simplicity)
  - *Enterprise Alternative*: TiKV (CNCF graduated) for distributed key-value with ACID transactions
- **Monitoring**: Prometheus (CNCF graduated) + Grafana + Jaeger (CNCF graduated)
- **Log Aggregation**: Fluentd (CNCF graduated)
- **CI/CD**: Argo CD (CNCF graduated) or GitHub Actions/GitLab CI

### Database Strategy
**Primary Recommendation**: PostgreSQL + Redis
- Optimized for developer productivity and operational simplicity
- Proven stack with excellent Python ecosystem support
- Suitable for most applications and scales well to medium-large deployments

**Enterprise Scale Alternatives**: Vitess + TiKV
- Consider when you need to handle massive scale (millions of users, petabytes of data)
- Requires significant operational expertise and infrastructure investment
- Migration path available when scale demands justify the complexity

## Environment Configuration

### Environment Types and Purposes
1. **Development**: Local development and testing
2. **Staging**: Pre-production testing and validation
3. **Production**: Live system serving real users
4. **DR (Disaster Recovery)**: Backup production environment

### Configuration Management
```yaml
# config/base.yaml - Common configuration
app:
  name: "coins-for-change"
  version: "1.0.0"
  
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30

redis:
  max_connections: 100
  socket_timeout: 5

opensearch:
  timeout: 30
  max_retries: 3

# config/production.yaml - Production overrides
database:
  pool_size: 50
  max_overflow: 100

logging:
  level: "INFO"
  format: "json"

security:
  jwt_expiration: 3600
  rate_limit_per_minute: 100
```

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=50

# Redis Configuration
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=100

# OpenSearch Configuration
OPENSEARCH_URL=https://host:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=secret

# Security Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

# External Services
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=smtp-password

# Monitoring
OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
PROMETHEUS_GATEWAY_URL=http://prometheus-pushgateway:9091

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

## Kubernetes Deployment

### Namespace and Resource Organization
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: coins-for-change
  labels:
    app: coins-for-change
    environment: production
```

### ConfigMap and Secrets
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: coins-for-change
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "https://app.example.com"
  
---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: coins-for-change
type: Opaque
data:
  DATABASE_URL: <base64-encoded-url>
  JWT_SECRET_KEY: <base64-encoded-secret>
  SMTP_PASSWORD: <base64-encoded-password>
```

### Service Deployment Example
```yaml
# auth-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: coins-for-change
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
        version: v1.0.0
    spec:
      containers:
      - name: auth-service
        image: coins-for-change/auth-service:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: SERVICE_NAME
          value: "auth-service"
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false

---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: coins-for-change
spec:
  selector:
    app: auth-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Database Deployment (PostgreSQL)
```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: coins-for-change
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: coins_for_change
        - name: POSTGRES_USER
          value: app_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

### Ingress Configuration (Envoy-based)
```yaml
# ingress.yaml - Using Envoy Gateway (CNCF graduated)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: app-gateway
  namespace: coins-for-change
spec:
  gatewayClassName: envoy-gateway
  listeners:
  - name: https
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs:
      - name: api-tls
    hostname: api.example.com
  - name: http
    port: 80
    protocol: HTTP
    hostname: api.example.com

---
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: app-routes
  namespace: coins-for-change
spec:
  parentRefs:
  - name: app-gateway
  hostnames:
  - api.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /auth
    backendRefs:
    - name: auth-service
      port: 80
  - matches:
    - path:
        type: PathPrefix
        value: /campaigns
    backendRefs:
    - name: campaign-service
      port: 80

---
# Alternative: Traditional Ingress with Envoy-based controller
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress-envoy
  namespace: coins-for-change
  annotations:
    kubernetes.io/ingress.class: envoy
    cert-manager.io/cluster-issuer: letsencrypt-prod
    envoy.ingress.kubernetes.io/rate-limit: "100"
    envoy.ingress.kubernetes.io/cors-allow-origin: "https://app.example.com"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /auth
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 80
      - path: /campaigns
        pathType: Prefix
        backend:
          service:
            name: campaign-service
            port:
              number: 80
```

## Database Management

### Migration Strategy
```python
# alembic/env.py configuration for multiple environments
def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    
    # Override with environment variables
    if os.getenv("DATABASE_URL"):
        configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Backup and Recovery
```bash
#!/bin/bash
# backup-database.sh

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-coins_for_change}
DB_USER=${DB_USER:-app_user}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql"

echo "Creating backup: ${BACKUP_FILE}"
pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    --verbose --clean --no-owner --no-privileges \
    --file=${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Upload to cloud storage (example with AWS S3)
aws s3 cp ${BACKUP_FILE}.gz s3://your-backup-bucket/database/

# Clean up old backups
find ${BACKUP_DIR} -name "backup_${DB_NAME}_*.sql.gz" \
    -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Database Monitoring
```yaml
# postgres-exporter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
  namespace: coins-for-change
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-exporter
  template:
    metadata:
      labels:
        app: postgres-exporter
    spec:
      containers:
      - name: postgres-exporter
        image: prometheuscommunity/postgres-exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: exporter-dsn
        ports:
        - containerPort: 9187
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
```

## Monitoring and Observability (CNCF Graduated Stack)

### Prometheus Configuration (CNCF Graduated)
```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
    
    - job_name: 'coins-for-change-services'
      static_configs:
      - targets:
        - 'auth-service:8000'
        - 'campaign-service:8000'
        - 'idea-service:8000'
        - 'coin-service:8000'
      metrics_path: '/metrics'
      scrape_interval: 10s
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Coins for Change - Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}} - {{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Coin Allocations per Hour",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(coin_allocations_total[1h])",
            "legendFormat": "Allocations"
          }
        ]
      }
    ]
  }
}
```

### Fluentd Log Aggregation (CNCF Graduated)
```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      serviceAccount: fluentd
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        - name: FLUENT_ELASTICSEARCH_SCHEME
          value: "http"
        - name: FLUENTD_SYSTEMD_CONF
          value: disable
        resources:
          limits:
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluentd-config
          mountPath: /fluentd/etc/fluent.conf
          subPath: fluent.conf
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluentd-config
        configMap:
          name: fluentd-config

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      @id in_tail_container_logs
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    <match kubernetes.var.log.containers.**coins-for-change**.log>
      @type elasticsearch
      host "#{ENV['FLUENT_ELASTICSEARCH_HOST']}"
      port "#{ENV['FLUENT_ELASTICSEARCH_PORT']}"
      scheme "#{ENV['FLUENT_ELASTICSEARCH_SCHEME']}"
      index_name coins-for-change-logs
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

### Jaeger Tracing (CNCF Graduated)
```yaml
# jaeger-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:latest
        ports:
        - containerPort: 16686
          name: ui
        - containerPort: 14268
          name: collector
        - containerPort: 6831
          name: agent-compact
        - containerPort: 6832
          name: agent-binary
        env:
        - name: COLLECTOR_OTLP_ENABLED
          value: "true"
        - name: SPAN_STORAGE_TYPE
          value: "elasticsearch"
        - name: ES_SERVER_URLS
          value: "http://elasticsearch:9200"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: monitoring
spec:
  selector:
    app: jaeger
  ports:
  - name: ui
    port: 16686
    targetPort: 16686
  - name: collector
    port: 14268
    targetPort: 14268
  - name: agent-compact
    port: 6831
    targetPort: 6831
    protocol: UDP
  - name: agent-binary
    port: 6832
    targetPort: 6832
    protocol: UDP
```

### Alerting Rules
```yaml
# alerting-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: monitoring
data:
  app-alerts.yml: |
    groups:
    - name: coins-for-change-alerts
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "Database has {{ $value }} active connections"
      
      - alert: CoinAllocationFailures
        expr: increase(coin_allocation_failures_total[10m]) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Multiple coin allocation failures"
          description: "{{ $value }} coin allocation failures in the last 10 minutes"
```

## Security Configuration

### Network Policies
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
  namespace: coins-for-change
spec:
  podSelector:
    matchLabels:
      app: auth-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Policy
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: coins-for-change-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## CI/CD Pipeline

### Argo CD GitOps (CNCF Graduated Alternative)
```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: coins-for-change
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/coins-for-change-platform
    targetRevision: main
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: coins-for-change
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

---
# argocd-project.yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: coins-for-change-project
  namespace: argocd
spec:
  description: Coins for Change Platform Project
  sourceRepos:
  - 'https://github.com/your-org/coins-for-change-platform'
  destinations:
  - namespace: coins-for-change
    server: https://kubernetes.default.svc
  - namespace: coins-for-change-staging
    server: https://kubernetes.default.svc
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  - group: 'rbac.authorization.k8s.io'
    kind: ClusterRole
  - group: 'rbac.authorization.k8s.io'
    kind: ClusterRoleBinding
  namespaceResourceWhitelist:
  - group: ''
    kind: '*'
  - group: 'apps'
    kind: '*'
  - group: 'networking.k8s.io'
    kind: '*'
```

### GitHub Actions Workflow (Alternative)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Tests
      run: |
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and Push Images
      env:
        REGISTRY: ghcr.io
        IMAGE_TAG: ${{ github.sha }}
      run: |
        echo ${{ secrets.GITHUB_TOKEN }} | docker login $REGISTRY -u ${{ github.actor }} --password-stdin
        
        # Build all service images
        for service in auth campaigns ideas coins search notifications analytics; do
          docker build -t $REGISTRY/${{ github.repository }}/$service:$IMAGE_TAG ./services/$service
          docker push $REGISTRY/${{ github.repository }}/$service:$IMAGE_TAG
        done

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        
        # Update image tags in deployment files
        sed -i "s/IMAGE_TAG_PLACEHOLDER/$IMAGE_TAG/g" k8s/production/*.yaml
        
        # Apply Kubernetes manifests
        kubectl apply -f k8s/production/
        
        # Wait for rollout to complete
        kubectl rollout status deployment/auth-service -n coins-for-change
        kubectl rollout status deployment/campaign-service -n coins-for-change
```

## Operational Procedures

### Health Checks and Readiness
```python
# health.py - Health check implementation
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import redis
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check - service is running"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/ready")
async def readiness_check():
    """Readiness check - service can handle requests"""
    checks = {}
    
    # Database check
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Redis check
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # OpenSearch check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OPENSEARCH_URL}/_cluster/health")
            if response.status_code == 200:
                checks["opensearch"] = "healthy"
            else:
                checks["opensearch"] = f"unhealthy: status {response.status_code}"
    except Exception as e:
        checks["opensearch"] = f"unhealthy: {str(e)}"
    
    # Overall status
    all_healthy = all(status == "healthy" for status in checks.values())
    
    if not all_healthy:
        raise HTTPException(status_code=503, detail=checks)
    
    return {"status": "ready", "checks": checks}
```

### Scaling Guidelines
```yaml
# horizontal-pod-autoscaler.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auth-service-hpa
  namespace: coins-for-change
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auth-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### Disaster Recovery Procedures
1. **Database Recovery**:
   - Restore from latest backup
   - Apply transaction logs if available
   - Verify data integrity
   - Update application configuration

2. **Service Recovery**:
   - Deploy from known good image tags
   - Verify all health checks pass
   - Gradually restore traffic
   - Monitor for issues

3. **Data Center Failover**:
   - Update DNS to point to DR environment
   - Restore database from cross-region backup
   - Deploy application services
   - Verify full functionality

### Maintenance Procedures
```bash
#!/bin/bash
# maintenance-mode.sh

# Enable maintenance mode
kubectl patch ingress app-ingress -n coins-for-change -p '
{
  "metadata": {
    "annotations": {
      "nginx.ingress.kubernetes.io/server-snippet": "return 503 \"Service temporarily unavailable for maintenance\";"
    }
  }
}'

# Perform maintenance tasks
echo "Maintenance mode enabled. Performing updates..."

# Scale down services
kubectl scale deployment --replicas=0 --all -n coins-for-change

# Run database migrations
kubectl run migration-job --image=coins-for-change/migration:latest \
  --restart=Never --rm -i --tty -- alembic upgrade head

# Scale services back up
kubectl scale deployment auth-service --replicas=3 -n coins-for-change
kubectl scale deployment campaign-service --replicas=3 -n coins-for-change

# Wait for services to be ready
kubectl wait --for=condition=available --timeout=300s deployment --all -n coins-for-change

# Disable maintenance mode
kubectl patch ingress app-ingress -n coins-for-change --type=json -p='[
  {
    "op": "remove",
    "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1server-snippet"
  }
]'

echo "Maintenance completed. Services are now available."
```