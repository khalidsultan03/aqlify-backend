import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main_v3 import app
from database import Base, get_db
from config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client():
    Base.metadata.create_all(bind=engine)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def test_user(client):
    """Create a test user and return access token"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "company_name": "Test Company",
        "industry": "Technology",
        "country": "Oman"
    }
    
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    return {
        "access_token": data["access_token"],
        "user_id": data["user"]["id"]
    }

@pytest.fixture
async def test_product(client, test_user):
    """Create a test product"""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    
    product_data = {
        "name": "Test Product",
        "category": "Electronics",
        "sku": "TEST-001",
        "unit_price": 99.99,
        "supplier": "Test Supplier",
        "lead_time_days": 7,
        "safety_stock_days": 5
    }
    
    response = await client.post("/products", json=product_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    return data["product"]["id"]

class TestAuthentication:
    
    async def test_register_user(self, client):
        user_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "company_name": "New Company"
        }
        
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == user_data["email"]
    
    async def test_register_duplicate_email(self, client, test_user):
        user_data = {
            "email": "test@example.com",  # Same as test_user
            "password": "password123",
            "company_name": "Another Company"
        }
        
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 400
    
    async def test_login_user(self, client, test_user):
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
    
    async def test_login_invalid_credentials(self, client):
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401

class TestProducts:
    
    async def test_create_product(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        product_data = {
            "name": "New Product",
            "category": "Technology",
            "sku": "NEW-001",
            "unit_price": 199.99
        }
        
        response = await client.post("/products", json=product_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["product"]["name"] == product_data["name"]
    
    async def test_get_products(self, client, test_user, test_product):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        response = await client.get("/products", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["products"]) >= 1
    
    async def test_unauthorized_access(self, client):
        response = await client.get("/products")
        assert response.status_code == 401

class TestSalesData:
    
    async def test_upload_sales_data(self, client, test_user, test_product):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        sales_data = {
            "product_id": test_product,
            "sales_data": [
                {"date": "2025-01-01", "quantity": 10, "revenue": 999.90},
                {"date": "2025-01-02", "quantity": 15, "revenue": 1499.85},
                {"date": "2025-01-03", "quantity": 8, "revenue": 799.92}
            ]
        }
        
        response = await client.post("/sales-data", json=sales_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "Successfully uploaded" in data["message"]

class TestForecasting:
    
    async def test_statistical_forecast(self, client, test_user, test_product):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        # First upload sales data
        sales_data = {
            "product_id": test_product,
            "sales_data": [
                {"date": f"2025-01-{i:02d}", "quantity": 10 + i}
                for i in range(1, 16)  # 15 days of data
            ]
        }
        
        await client.post("/sales-data", json=sales_data, headers=headers)
        
        # Generate forecast
        forecast_request = {
            "product_id": test_product,
            "forecast_days": 7,
            "method": "statistical",
            "include_external_data": False
        }
        
        response = await client.post("/forecast", json=forecast_request, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "forecasts" in data
        assert len(data["forecasts"]) == 7
    
    async def test_scenario_forecast(self, client, test_user, test_product):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        # Upload sales data first
        sales_data = {
            "product_id": test_product,
            "sales_data": [
                {"date": f"2025-01-{i:02d}", "quantity": 10}
                for i in range(1, 16)
            ]
        }
        
        await client.post("/sales-data", json=sales_data, headers=headers)
        
        # Generate scenario forecast
        scenario_request = {
            "product_id": test_product,
            "forecast_days": 7,
            "scenario": {
                "demand_change_percent": 20,
                "weather_impact": "rain",
                "economic_impact": "growth"
            }
        }
        
        response = await client.post("/forecast/scenario", json=scenario_request, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "forecast" in data
        assert "scenario" in data

class TestDashboard:
    
    async def test_dashboard(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        response = await client.get("/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "recent_forecasts" in data
    
    async def test_get_alerts(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        response = await client.get("/alerts", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data

class TestApiEndpoints:
    
    async def test_root_endpoint(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "Aqlify Universal Forecasting Platform" in data["message"]
    
    async def test_user_profile(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        response = await client.get("/user/profile", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "test@example.com"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
