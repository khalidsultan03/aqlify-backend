# Deployment Guide for Aqlify Universal Forecasting Platform

## 🚀 Production Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Prerequisites**:
   - Docker and Docker Compose installed
   - Domain name configured (optional)
   - SSL certificates (for HTTPS)

2. **Quick Start**:
   ```bash
   # Clone repository
   git clone <repo-url>
   cd aqlify-backend
   
   # Configure environment
   cp env_production.txt .env
   nano .env  # Edit with your API keys and settings
   
   # Deploy with Docker
   docker-compose up -d
   
   # Check status
   docker-compose ps
   ```

3. **Environment Variables**:
   ```env
   DATABASE_URL=postgresql://aqlify_user:secure_password@postgres:5432/aqlify_production
   REDIS_URL=redis://redis:6379
   OPENAI_API_KEY=sk-your-openai-key
   WEATHER_API_KEY=your-weather-api-key
   NEWS_API_KEY=your-news-api-key
   SECRET_KEY=your-256-bit-secret-key
   ```

### Option 2: Cloud Platform Deployment

#### AWS Deployment
```bash
# Using AWS ECS + RDS + ElastiCache
aws ecs create-cluster --cluster-name aqlify-cluster
aws rds create-db-instance --db-instance-identifier aqlify-db
aws elasticache create-cache-cluster --cache-cluster-id aqlify-redis
```

#### Google Cloud Deployment
```bash
# Using Cloud Run + Cloud SQL + Memorystore
gcloud run deploy aqlify-api --image gcr.io/PROJECT/aqlify
gcloud sql instances create aqlify-postgres
gcloud redis instances create aqlify-redis
```

#### Azure Deployment
```bash
# Using Container Instances + PostgreSQL + Redis Cache
az container create --name aqlify-api
az postgres server create --name aqlify-postgres
az redis create --name aqlify-redis
```

### Option 3: Manual Server Deployment

1. **Server Setup** (Ubuntu 20.04+):
   ```bash
   # Install dependencies
   sudo apt update
   sudo apt install python3.11 python3-pip postgresql redis-server nginx
   
   # Setup PostgreSQL
   sudo -u postgres createuser aqlify_user
   sudo -u postgres createdb aqlify_production
   
   # Clone and setup application
   git clone <repo-url>
   cd aqlify-backend
   pip install -r requirements_v3.txt
   
   # Setup environment
   cp env_production.txt .env
   nano .env
   
   # Run with Gunicorn
   gunicorn main_v3:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Nginx Configuration**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔧 Configuration Management

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI forecasting | Yes |
| `WEATHER_API_KEY` | Weather API key | Optional |
| `NEWS_API_KEY` | News API key | Optional |
| `SECRET_KEY` | JWT secret key (256-bit) | Yes |

### API Keys Setup
1. **OpenAI**: Get from https://platform.openai.com/api-keys
2. **Weather API**: Get from https://www.weatherapi.com/
3. **News API**: Get from https://newsapi.org/

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check application health
curl http://localhost:8000/

# Check database connection
docker exec postgres pg_isready

# Check Redis
docker exec redis redis-cli ping
```

### Logging
```bash
# View application logs
docker-compose logs -f api

# View database logs
docker-compose logs -f postgres

# View Redis logs
docker-compose logs -f redis
```

### Backup Strategy
```bash
# Database backup
docker exec postgres pg_dump -U aqlify_user aqlify_production > backup.sql

# Redis backup
docker exec redis redis-cli BGSAVE
```

## 🔒 Security Checklist

- [ ] Change default passwords
- [ ] Use HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable database SSL
- [ ] Use secrets management
- [ ] Configure CORS properly
- [ ] Set up monitoring alerts

## 📈 Scaling Considerations

### Horizontal Scaling
- Load balance multiple API instances
- Use Redis for session sharing
- Database connection pooling
- CDN for static assets

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Implement caching strategies
- Monitor performance metrics

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL status
   docker-compose logs postgres
   
   # Test connection
   psql $DATABASE_URL
   ```

2. **API Key Issues**:
   ```bash
   # Verify environment variables
   docker exec api env | grep API_KEY
   ```

3. **Performance Issues**:
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check API response times
   curl -w "@curl-format.txt" http://localhost:8000/
   ```

## 🎯 Next Steps

1. Set up monitoring (Prometheus + Grafana)
2. Implement automated backups
3. Configure CI/CD pipeline
4. Set up staging environment
5. Implement advanced analytics
6. Add more external data sources

## 📞 Support

For production deployment support:
- Check documentation at `/docs` endpoint
- Review logs for error details
- Monitor system resources
- Contact technical support for enterprise customers
