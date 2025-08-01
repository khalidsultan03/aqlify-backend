# Aqlify Universal Forecasting Platform

## 🚀 Production-Ready SaaS Forecasting Solution

A comprehensive, multi-tenant demand forecasting platform that any business can use to predict demand, optimize inventory, and make data-driven decisions.

### ✨ Key Features

- **Multi-Tenant SaaS Architecture** - Each business gets their own isolated data
- **Advanced AI Forecasting** - OpenAI-powered predictions with multiple algorithms
- **Real-Time Alerts** - Automatic detection of demand anomalies and stockout risks
- **External Data Integration** - Weather, economic indicators, and news sentiment
- **Scenario Planning** - "What-if" analysis for different business conditions
- **Multi-Algorithm Ensemble** - Statistical, AI, and hybrid forecasting methods
- **Subscription Tiers** - Free, Premium, and Enterprise plans
- **RESTful API** - Easy integration with existing business systems

### 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend App  │    │  External APIs  │    │   Admin Panel   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────────────────┘
                     │
        ┌─────────────────────────────────────────────────┐
        │              FastAPI Backend                    │
        │  ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
        │  │ Auth System │ │ Forecasting │ │  Alerts   │ │
        │  └─────────────┘ └─────────────┘ └───────────┘ │
        └─────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴───────────────┐
        │                             │
┌───────▼───────┐           ┌─────────▼─────────┐
│  PostgreSQL   │           │      Redis        │
│   Database    │           │      Cache        │
└───────────────┘           └───────────────────┘
```

### 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management and caching
- **AI**: OpenAI GPT-4 for advanced forecasting
- **External APIs**: Weather API, News API, Economic indicators
- **Authentication**: JWT with bcrypt password hashing
- **Deployment**: Docker, Docker Compose
- **Testing**: Pytest with async support

### 📦 Quick Start

#### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

#### 1. Clone and Setup

```bash
git clone <repository-url>
cd aqlify-backend
```

#### 2. Environment Configuration

```bash
cp env_production.txt .env
```

Edit `.env` with your configuration:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/aqlify_db
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-openai-api-key
WEATHER_API_KEY=your-weather-api-key
NEWS_API_KEY=your-news-api-key
SECRET_KEY=your-super-secret-jwt-key
```

#### 3. Install Dependencies

```bash
pip install -r requirements_v3.txt
```

#### 4. Run with Docker (Recommended)

```bash
docker-compose up -d
```

#### 5. Or Run Manually

```bash
# Start PostgreSQL and Redis
# Then run:
uvicorn main_v3:app --host 0.0.0.0 --port 8000 --reload
```

### 📖 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### 🔑 API Endpoints

#### Authentication
- `POST /auth/register` - Register new business
- `POST /auth/login` - User login
- `GET /user/profile` - Get user profile

#### Product Management
- `POST /products` - Create product
- `GET /products` - List all products
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

#### Sales Data
- `POST /sales-data` - Upload bulk sales data

#### Forecasting
- `POST /forecast` - Generate demand forecast
- `POST /forecast/scenario` - Generate scenario-based forecast

#### Alerts & Insights
- `GET /alerts` - Get business alerts
- `POST /alerts/{id}/read` - Mark alert as read
- `POST /alerts/{id}/resolve` - Resolve alert

#### Dashboard
- `GET /dashboard` - Get business dashboard summary

### 🎯 Usage Examples

#### 1. Register a Business

```python
import requests

# Register
response = requests.post("http://localhost:8000/auth/register", json={
    "email": "owner@mybusiness.com",
    "password": "securepassword123",
    "company_name": "My Business Inc",
    "industry": "Retail",
    "country": "Oman"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

#### 2. Add Products

```python
# Create product
product_response = requests.post("http://localhost:8000/products", 
    headers=headers,
    json={
        "name": "Premium Coffee Beans",
        "category": "Food & Beverage",
        "sku": "COFFEE-001",
        "unit_price": 25.99,
        "supplier": "Local Coffee Roasters",
        "lead_time_days": 5,
        "safety_stock_days": 7
    }
)

product_id = product_response.json()["product"]["id"]
```

#### 3. Upload Sales Data

```python
# Upload historical sales
sales_response = requests.post("http://localhost:8000/sales-data",
    headers=headers,
    json={
        "product_id": product_id,
        "sales_data": [
            {"date": "2025-01-01", "quantity": 50, "revenue": 1299.50, "channel": "retail"},
            {"date": "2025-01-02", "quantity": 45, "revenue": 1169.55, "channel": "retail"},
            # ... more data
        ]
    }
)
```

#### 4. Generate Forecast

```python
# AI-powered forecast
forecast_response = requests.post("http://localhost:8000/forecast",
    headers=headers,
    json={
        "product_id": product_id,
        "forecast_days": 30,
        "method": "ai",
        "include_external_data": True,
        "user_notes": "Expecting increased demand due to new marketing campaign"
    }
)

forecast = forecast_response.json()
print(f"30-day forecast confidence: {forecast['confidence']}")
print(f"Recommended reorder quantity: {forecast['reorder_quantity']}")
```

#### 5. Scenario Planning

```python
# What-if analysis
scenario_response = requests.post("http://localhost:8000/forecast/scenario",
    headers=headers,
    json={
        "product_id": product_id,
        "forecast_days": 14,
        "scenario": {
            "demand_change_percent": 25,  # 25% increase
            "weather_impact": "rain",     # Rainy weather
            "economic_impact": "growth"   # Economic growth
        }
    }
)
```

### 🔒 Security Features

- **JWT Authentication** with secure token expiration
- **Password Hashing** using bcrypt
- **Rate Limiting** to prevent API abuse
- **Input Validation** with Pydantic models
- **SQL Injection Protection** via SQLAlchemy ORM
- **CORS Configuration** for cross-origin requests

### 📊 Subscription Tiers

| Feature | Free | Premium | Enterprise |
|---------|------|---------|------------|
| Monthly Forecasts | 100 | 1,000 | 10,000 |
| Products | 5 | 50 | Unlimited |
| External Data | ❌ | ✅ | ✅ |
| Scenario Planning | ❌ | ✅ | ✅ |
| Real-time Alerts | Basic | Advanced | Advanced |
| API Access | Limited | Full | Full |
| Priority Support | ❌ | ✅ | ✅ |

### 🧪 Testing

Run the comprehensive test suite:

```bash
pytest test_main.py -v
```

Tests cover:
- Authentication and authorization
- Product management
- Sales data upload
- Forecasting algorithms
- API endpoints
- Error handling

### 🚀 Deployment

#### Production Deployment with Docker

1. **Set up production environment**:
```bash
cp env_production.txt .env
# Edit .env with production values
```

2. **Deploy with Docker Compose**:
```bash
docker-compose up -d
```

3. **Set up reverse proxy** (nginx configuration included)

4. **Configure SSL certificates** for HTTPS

#### Cloud Deployment Options

- **AWS**: ECS + RDS + ElastiCache
- **Google Cloud**: Cloud Run + Cloud SQL + Memorystore
- **Azure**: Container Instances + PostgreSQL + Redis Cache
- **Digital Ocean**: App Platform + Managed Databases

### 📈 Monitoring & Analytics

- **Health Checks**: Built-in health endpoints
- **Logging**: Structured logging for production monitoring
- **Metrics**: Usage tracking and business intelligence
- **Alerts**: Real-time business and system alerts

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

### 🆘 Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Enterprise Support**: Contact for dedicated support

### 🎯 Roadmap

- [ ] Machine Learning model training on user data
- [ ] Mobile app for iOS and Android
- [ ] Advanced visualization dashboard
- [ ] Integration with major ERP systems
- [ ] Blockchain supply chain tracking
- [ ] IoT sensor integration
- [ ] Advanced analytics and reporting
- [ ] Multi-language support

---

**Built with ❤️ for businesses worldwide to make smarter demand forecasting decisions.**
