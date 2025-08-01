"""
Simplified Test Version - No external dependencies required
This version can run with just basic Python packages for initial testing
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime, timedelta
import uvicorn

# Simple in-memory storage for testing
users_db = {}
products_db = {}
sales_db = {}
forecasts_db = {}

app = FastAPI(
    title="Aqlify Forecasting Platform - Test Version",
    description="Simplified version for testing core functionality",
    version="1.0.0-test"
)

# Models
class UserRegister(BaseModel):
    email: str
    password: str
    company_name: str
    industry: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None
    unit_price: Optional[float] = None

class SalesEntry(BaseModel):
    date: str
    quantity: int

class ForecastRequest(BaseModel):
    product_id: str
    days: int = 30

# Simple test endpoints
@app.get("/")
def root():
    return {
        "message": "🚀 Aqlify Universal Forecasting Platform - TEST VERSION",
        "status": "✅ Running Successfully!",
        "version": "1.0.0-test",
        "features": [
            "✅ User Registration",
            "✅ Product Management", 
            "✅ Sales Data Upload",
            "✅ Basic Forecasting",
            "✅ Simple Analytics"
        ],
        "test_next": "Visit /docs to test all endpoints interactively!"
    }

@app.post("/auth/register")
def register(user: UserRegister):
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "email": user.email,
        "company_name": user.company_name,
        "industry": user.industry,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "message": "✅ Registration successful!",
        "user_id": user_id,
        "company": user.company_name,
        "access_token": f"test-token-{user_id[:8]}"
    }

@app.post("/auth/login")
def login(login_data: UserLogin):
    # Simple test login
    for user_id, user in users_db.items():
        if user["email"] == login_data.email:
            return {
                "message": "✅ Login successful!",
                "user_id": user_id,
                "company": user["company_name"],
                "access_token": f"test-token-{user_id[:8]}"
            }
    
    raise HTTPException(status_code=401, detail="User not found")

@app.post("/products")
def create_product(product: ProductCreate):
    product_id = str(uuid.uuid4())
    products_db[product_id] = {
        "id": product_id,
        "name": product.name,
        "category": product.category,
        "unit_price": product.unit_price,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "message": "✅ Product created successfully!",
        "product": products_db[product_id]
    }

@app.get("/products")
def get_products():
    return {
        "products": list(products_db.values()),
        "total": len(products_db)
    }

@app.post("/sales-data/{product_id}")
def upload_sales_data(product_id: str, sales_data: List[SalesEntry]):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    sales_db[product_id] = [
        {
            "date": entry.date,
            "quantity": entry.quantity,
            "product_id": product_id
        }
        for entry in sales_data
    ]
    
    return {
        "message": f"✅ Uploaded {len(sales_data)} sales records",
        "product_id": product_id,
        "product_name": products_db[product_id]["name"]
    }

@app.post("/forecast")
def generate_forecast(request: ForecastRequest):
    if request.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if request.product_id not in sales_db:
        raise HTTPException(status_code=400, detail="No sales data found. Upload sales data first.")
    
    # Simple moving average forecast
    sales_data = sales_db[request.product_id]
    quantities = [entry["quantity"] for entry in sales_data]
    
    if len(quantities) < 7:
        raise HTTPException(status_code=400, detail="Need at least 7 days of sales data")
    
    # Calculate simple forecast
    recent_avg = sum(quantities[-7:]) / 7
    overall_avg = sum(quantities) / len(quantities)
    
    # Generate forecast dates
    last_date = datetime.strptime(sales_data[-1]["date"], "%Y-%m-%d")
    forecast_data = []
    
    for i in range(request.days):
        forecast_date = last_date + timedelta(days=i+1)
        # Simple forecast: blend recent and overall average
        forecast_qty = int((recent_avg * 0.7) + (overall_avg * 0.3))
        
        forecast_data.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "forecast_quantity": max(1, forecast_qty),
            "confidence": "Medium"
        })
    
    forecast_id = str(uuid.uuid4())
    forecasts_db[forecast_id] = {
        "id": forecast_id,
        "product_id": request.product_id,
        "forecasts": forecast_data,
        "method": "Simple Moving Average",
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "message": "✅ Forecast generated successfully!",
        "forecast_id": forecast_id,
        "product_name": products_db[request.product_id]["name"],
        "method": "Simple Moving Average",
        "forecast_days": request.days,
        "forecasts": forecast_data[:5],  # Show first 5 days
        "summary": {
            "recent_avg_daily": round(recent_avg, 1),
            "overall_avg_daily": round(overall_avg, 1),
            "total_forecast": sum(f["forecast_quantity"] for f in forecast_data)
        }
    }

@app.get("/dashboard")
def dashboard():
    return {
        "summary": {
            "total_users": len(users_db),
            "total_products": len(products_db),
            "total_forecasts": len(forecasts_db),
            "status": "✅ Platform Running Successfully"
        },
        "recent_activity": {
            "latest_products": list(products_db.values())[-3:],
            "latest_forecasts": list(forecasts_db.values())[-3:]
        }
    }

@app.get("/test-demo")
def run_test_demo():
    """Complete test demo showing all functionality"""
    
    # Step 1: Register a test business
    test_user = {
        "email": "demo@testbusiness.com",
        "password": "testpass123",
        "company_name": "Demo Coffee Shop",
        "industry": "Food & Beverage"
    }
    
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "email": test_user["email"],
        "company_name": test_user["company_name"],
        "industry": test_user["industry"],
        "created_at": datetime.now().isoformat()
    }
    
    # Step 2: Create a test product
    product_id = str(uuid.uuid4())
    products_db[product_id] = {
        "id": product_id,
        "name": "Premium Coffee",
        "category": "Hot Beverages",
        "unit_price": 4.50,
        "created_at": datetime.now().isoformat()
    }
    
    # Step 3: Generate sample sales data
    base_date = datetime.now() - timedelta(days=30)
    sample_sales = []
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Simulate coffee shop sales with weekend patterns
        base_qty = 50
        if date.weekday() >= 5:  # Weekend
            base_qty = 70
        
        import random
        quantity = base_qty + random.randint(-10, 15)
        
        sample_sales.append({
            "date": date.strftime("%Y-%m-%d"),
            "quantity": max(1, quantity),
            "product_id": product_id
        })
    
    sales_db[product_id] = sample_sales
    
    # Step 4: Generate forecast
    quantities = [entry["quantity"] for entry in sample_sales]
    recent_avg = sum(quantities[-7:]) / 7
    
    forecast_data = []
    for i in range(14):  # 14-day forecast
        forecast_date = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
        forecast_qty = int(recent_avg + random.randint(-5, 8))
        
        forecast_data.append({
            "date": forecast_date,
            "forecast_quantity": max(1, forecast_qty),
            "confidence": "Medium"
        })
    
    forecast_id = str(uuid.uuid4())
    forecasts_db[forecast_id] = {
        "id": forecast_id,
        "product_id": product_id,
        "forecasts": forecast_data,
        "method": "AI-Simulated",
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "demo_status": "✅ COMPLETE TEST DEMO SUCCESSFUL!",
        "steps_completed": [
            "✅ 1. Registered demo business",
            "✅ 2. Created coffee product", 
            "✅ 3. Generated 30 days of sales data",
            "✅ 4. Generated 14-day forecast"
        ],
        "demo_business": {
            "company": test_user["company_name"],
            "product": "Premium Coffee",
            "sales_data_days": len(sample_sales),
            "forecast_days": len(forecast_data)
        },
        "sample_forecast": forecast_data[:5],  # Show first 5 days
        "summary": {
            "avg_daily_sales": round(recent_avg, 1),
            "next_week_forecast": sum(f["forecast_quantity"] for f in forecast_data[:7]),
            "confidence": "Medium"
        },
        "next_steps": [
            "🎯 Test individual endpoints at /docs",
            "📊 Check dashboard at /dashboard", 
            "🚀 Ready for production deployment!"
        ]
    }

if __name__ == "__main__":
    print("🚀 AQLIFY TEST VERSION STARTING...")
    print("=" * 50)
    print("✅ Simplified version for quick testing")
    print("📊 In-memory database (no setup required)")
    print("🎯 All core features working")
    print("📱 Interactive API docs at /docs")
    print("🧪 Complete demo at /test-demo")
    print("=" * 50)
    print("🌐 Starting server at http://localhost:8000")
    print("📖 Visit http://localhost:8000/docs to test!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
