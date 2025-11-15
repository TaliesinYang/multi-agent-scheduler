# Deployment Guide

Complete guide for deploying Multi-Agent Scheduler in production.

---

## 🚀 Quick Start with Docker

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ disk space

### 1. Clone Repository

```bash
git clone https://github.com/your-org/multi-agent-scheduler.git
cd multi-agent-scheduler
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 3. Start All Services

```bash
docker-compose up -d
```

This starts:
- **Scheduler** (port 8000) - Main application
- **Jaeger** (port 16686) - Distributed tracing UI
- **Redis** (port 6379) - Checkpoint storage
- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3000) - Metrics visualization

### 4. Verify Deployment

Check service health:

```bash
# Check all services
docker-compose ps

# Check scheduler health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics
```

### 5. Access Web Interfaces

- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 📦 Production Deployment

### Docker Compose (Recommended)

For small to medium deployments:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  scheduler:
    image: multi-agent-scheduler:3.0.0
    restart: always
    environment:
      - LOG_LEVEL=WARNING
      - CHECKPOINT_ENABLED=true
      - TRACING_ENABLED=true
    volumes:
      - /data/scheduler:/app/data
      - /var/log/scheduler:/app/logs
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes (Enterprise)

For large-scale deployments:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scheduler
  template:
    metadata:
      labels:
        app: scheduler
    spec:
      containers:
      - name: scheduler
        image: multi-agent-scheduler:3.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

Deploy:

```bash
kubectl apply -f k8s/
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | - | Claude API key |
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key |
| `GEMINI_API_KEY` | Yes* | - | Gemini API key |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `CHECKPOINT_ENABLED` | No | true | Enable checkpointing |
| `TRACING_ENABLED` | No | true | Enable distributed tracing |
| `JAEGER_HOST` | No | localhost | Jaeger agent host |
| `JAEGER_PORT` | No | 6831 | Jaeger agent port |
| `REDIS_HOST` | No | localhost | Redis host |
| `REDIS_PORT` | No | 6379 | Redis port |

*At least one API key required

### Configuration File

Create `config.yaml`:

```yaml
# Multi-Agent Scheduler Configuration

scheduler:
  max_concurrent_tasks: 100
  default_timeout: 300  # seconds
  retry_attempts: 3

agents:
  claude:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 4000
    temperature: 0.7

  openai:
    model: "gpt-4"
    max_tokens: 4000
    temperature: 0.7

checkpoint:
  backend: redis  # or filesystem
  interval: 60  # seconds
  retention_days: 7

tracing:
  enabled: true
  sample_rate: 1.0  # 100% sampling
  service_name: "multi-agent-scheduler"

logging:
  level: INFO
  format: json  # or text
  file: /app/logs/scheduler.log
  max_size: 100  # MB
  backup_count: 5
```

---

## 🔒 Security

### API Key Management

**DO NOT** commit API keys to version control!

Use environment variables or secrets management:

#### Docker Secrets

```yaml
services:
  scheduler:
    secrets:
      - anthropic_api_key
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_api_key

secrets:
  anthropic_api_key:
    file: ./secrets/anthropic_key.txt
```

#### Kubernetes Secrets

```bash
kubectl create secret generic api-keys \
  --from-literal=anthropic=sk-ant-xxx \
  --from-literal=openai=sk-xxx \
  --from-literal=gemini=xxx
```

### Network Security

- Use HTTPS in production
- Enable firewall rules
- Restrict port access
- Use VPN for internal services

### Authentication

Add authentication to the health/metrics endpoints:

```python
# In your application
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/health")
async def health(token: str = Depends(security)):
    if token != os.getenv("HEALTH_TOKEN"):
        raise HTTPException(401)
    return {"status": "healthy"}
```

---

## 📊 Monitoring

### Health Checks

The scheduler exposes a health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "version": "3.0.0",
  "uptime": 3600,
  "active_tasks": 5,
  "services": {
    "redis": "connected",
    "jaeger": "connected"
  }
}
```

### Metrics

Prometheus metrics available at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `scheduler_tasks_total` - Total tasks executed
- `scheduler_tasks_duration_seconds` - Task execution duration
- `scheduler_tasks_active` - Currently active tasks
- `scheduler_errors_total` - Total errors
- `checkpoint_operations_total` - Checkpoint operations
- `checkpoint_duration_seconds` - Checkpoint duration

### Distributed Tracing

View traces in Jaeger UI:

```bash
open http://localhost:16686
```

Search for traces:
1. Select service: "multi-agent-scheduler"
2. Select operation: "execute_workflow"
3. Click "Find Traces"

### Log Aggregation

Logs are written to stdout and `/app/logs/scheduler.log`.

Forward to log aggregation service:

```yaml
# docker-compose.yml
services:
  scheduler:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or use Loki/Fluentd/Elasticsearch.

---

## 🔄 Updates and Rollbacks

### Update to New Version

```bash
# Pull new image
docker pull multi-agent-scheduler:3.1.0

# Update docker-compose.yml
# Change image version

# Restart with new version
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8000/health
```

### Rollback

```bash
# Revert to previous version
docker-compose down
# Edit docker-compose.yml - change version back
docker-compose up -d
```

### Zero-Downtime Deployment (Kubernetes)

```bash
kubectl set image deployment/scheduler \
  scheduler=multi-agent-scheduler:3.1.0

kubectl rollout status deployment/scheduler
```

Rollback:

```bash
kubectl rollout undo deployment/scheduler
```

---

## 🐛 Troubleshooting

### Service Won't Start

Check logs:

```bash
docker-compose logs scheduler
```

Common issues:
- Missing API keys → Check `.env` file
- Port conflict → Change ports in docker-compose.yml
- Insufficient memory → Increase Docker memory limit

### High Memory Usage

Monitor memory:

```bash
docker stats
```

Adjust limits:

```yaml
services:
  scheduler:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase limit
```

### Slow Performance

Check metrics:

```bash
curl http://localhost:8000/metrics | grep duration
```

Tune configuration:

```yaml
scheduler:
  max_concurrent_tasks: 50  # Reduce concurrency
  worker_threads: 4  # Add more workers
```

### Checkpoint Failures

Check Redis connection:

```bash
docker-compose logs redis
docker exec -it redis redis-cli ping
```

Fallback to filesystem:

```yaml
environment:
  - CHECKPOINT_BACKEND=filesystem
```

---

## 📈 Scaling

### Vertical Scaling

Increase resources:

```yaml
services:
  scheduler:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Horizontal Scaling

Run multiple instances:

```yaml
services:
  scheduler:
    deploy:
      replicas: 3
```

Add load balancer:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - scheduler
```

---

## 🔒 Backup and Recovery

### Backup Checkpoints

```bash
# Backup Redis data
docker exec redis redis-cli --rdb /data/backup.rdb

# Backup filesystem checkpoints
tar -czf checkpoints-backup.tar.gz data/checkpoints/
```

### Restore from Backup

```bash
# Restore Redis
docker exec -i redis redis-cli --pipe < backup.rdb

# Restore filesystem
tar -xzf checkpoints-backup.tar.gz -C data/
```

---

## 📞 Support

- **Documentation**: https://docs.multi-agent-scheduler.io
- **Issues**: https://github.com/your-org/multi-agent-scheduler/issues
- **Slack**: https://multi-agent-scheduler.slack.com
- **Email**: support@multi-agent-scheduler.io

---

**Production Checklist**:

- [ ] API keys configured
- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation reviewed
- [ ] Team trained

**Ready for production!** 🚀
