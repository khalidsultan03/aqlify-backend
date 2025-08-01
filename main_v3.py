from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import asyncio

from config import settings
from database import get_db, create_tables, User, Product, SalesData, Forecast, Alert
from auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, check_usage_limit, log_usage
)
from forecasting import forecasting_engine
from external_data import external_data_collector
from alerts import alert_system

# Initialize FastAPI app
app = FastAPI(
    title="Aqlify Universal Forecasting Platform",
    description="Advanced AI-powered demand forecasting for any business",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    company_name: str = Field(..., min_length=1)
    industry: Optional[str] = None
    country: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category: Optional[str] = None
    sku: Optional[str] = None
    unit_price: Optional[float] = None
    supplier: Optional[str] = None
    lead_time_days: int = Field(default=7, ge=1, le=365)
    safety_stock_days: int = Field(default=7, ge=1, le=90)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    unit_price: Optional[float] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = Field(None, ge=1, le=365)
    safety_stock_days: Optional[int] = Field(None, ge=1, le=90)

class SalesDataEntry(BaseModel):
    date: str  # YYYY-MM-DD format
    quantity: int = Field(..., ge=0)
    revenue: Optional[float] = None
    channel: Optional[str] = None
    region: Optional[str] = None

class SalesDataBulk(BaseModel):
    product_id: str
    sales_data: List[SalesDataEntry] = Field(..., min_length=1)

class ForecastRequest(BaseModel):
    product_id: str
    forecast_days: int = Field(default=30, ge=1, le=365)
    method: str = Field(default="ai", regex="^(ai|statistical|hybrid)$")
    include_external_data: bool = True
    user_notes: Optional[str] = None

class ScenarioForecastRequest(BaseModel):
    product_id: str
    forecast_days: int = Field(default=30, ge=1, le=365)
    scenario: Dict[str, Any]

class ForecastResponse(BaseModel):
    forecast_id: str
    product_id: str
    forecasts: List[Dict[str, Any]]
    method: str
    confidence: str
    reorder_quantity: Optional[int] = None
    key_factors: Optional[List[str]] = None
    risk_assessment: Optional[str] = None
    recommendations: Optional[List[str]] = None
    explanation: Optional[str] = None
    created_at: datetime

# Create database tables
create_tables()

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Aqlify Universal Forecasting Platform",
        "version": "3.0.0",
        "status": "active",
        "features": [
            "Multi-tenant SaaS architecture",
            "AI-powered forecasting",
            "Real-time alerts",
            "External data integration",
            "Scenario planning",
            "Multi-algorithm ensemble"
        ]
    }

@app.post("/auth/register")
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email.lower(),
        hashed_password=hashed_password,
        company_name=user_data.company_name,
        industry=user_data.industry,
        country=user_data.country,
        subscription_tier="free"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate access token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "company_name": new_user.company_name,
            "subscription_tier": new_user.subscription_tier
        }
    }

@app.post("/auth/login")
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == user_data.email.lower()).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "company_name": user.company_name,
            "subscription_tier": user.subscription_tier
        }
    }

@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "company_name": current_user.company_name,
        "industry": current_user.industry,
        "country": current_user.country,
        "subscription_tier": current_user.subscription_tier,
        "created_at": current_user.created_at
    }

@app.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    new_product = Product(
        user_id=current_user.id,
        name=product_data.name,
        category=product_data.category,
        sku=product_data.sku,
        unit_price=product_data.unit_price,
        supplier=product_data.supplier,
        lead_time_days=product_data.lead_time_days,
        safety_stock_days=product_data.safety_stock_days
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {
        "message": "Product created successfully",
        "product": {
            "id": new_product.id,
            "name": new_product.name,
            "category": new_product.category,
            "sku": new_product.sku,
            "created_at": new_product.created_at
        }
    }

@app.get("/products")
async def get_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user's products"""
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    
    return {
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "sku": product.sku,
                "unit_price": product.unit_price,
                "supplier": product.supplier,
                "lead_time_days": product.lead_time_days,
                "safety_stock_days": product.safety_stock_days,
                "created_at": product.created_at
            }
            for product in products
        ]
    }

@app.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update fields
    for field, value in product_data.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return {"message": "Product updated successfully"}

@app.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}

@app.post("/sales-data")
async def upload_sales_data(
    sales_data: SalesDataBulk,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload bulk sales data"""
    # Verify product belongs to user
    product = db.query(Product).filter(
        Product.id == sales_data.product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Insert sales data
    sales_entries = []
    for entry in sales_data.sales_data:
        try:
            sale_date = datetime.strptime(entry.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format: {entry.date}. Use YYYY-MM-DD"
            )
        
        sales_entry = SalesData(
            product_id=sales_data.product_id,
            date=sale_date,
            quantity=entry.quantity,
            revenue=entry.revenue,
            channel=entry.channel,
            region=entry.region
        )
        sales_entries.append(sales_entry)
    
    db.add_all(sales_entries)
    db.commit()
    
    return {
        "message": f"Successfully uploaded {len(sales_entries)} sales records",
        "product_id": sales_data.product_id
    }

@app.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    forecast_request: ForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate demand forecast"""
    # Check usage limits
    if not check_usage_limit(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly forecast limit reached for {current_user.subscription_tier} tier"
        )
    
    # Verify product belongs to user
    product = db.query(Product).filter(
        Product.id == forecast_request.product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get sales data
    sales_data = db.query(SalesData).filter(
        SalesData.product_id == forecast_request.product_id
    ).order_by(SalesData.date).all()
    
    if len(sales_data) < settings.MIN_HISTORICAL_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least {settings.MIN_HISTORICAL_DAYS} days of sales data required"
        )
    
    # Prepare sales data for forecasting
    sales_list = [
        {
            "date": sale.date.strftime("%Y-%m-%d"),
            "quantity": sale.quantity
        }
        for sale in sales_data
    ]
    
    # Collect external data if requested
    external_data = {}
    if forecast_request.include_external_data:
        try:
            region = sales_data[0].region if sales_data and sales_data[0].region else "Oman"
            external_data = await external_data_collector.collect_all_external_data(
                region, product.category or "general", db
            )
        except Exception as e:
            print(f"External data collection failed: {e}")
    
    # Generate forecast based on method
    if forecast_request.method == "statistical":
        forecast_result = forecasting_engine.calculate_statistical_forecast(
            sales_list, forecast_request.forecast_days
        )
    elif forecast_request.method == "ai":
        forecast_result = await forecasting_engine.generate_ai_forecast(
            product, sales_list, external_data, forecast_request.user_notes
        )
    else:  # hybrid
        # Combine both methods
        statistical_result = forecasting_engine.calculate_statistical_forecast(
            sales_list, forecast_request.forecast_days
        )
        ai_result = await forecasting_engine.generate_ai_forecast(
            product, sales_list, external_data, forecast_request.user_notes
        )
        
        # Simple ensemble (average)
        forecast_result = {
            "dates": statistical_result["dates"],
            "quantities": [
                int((stat + ai) / 2) 
                for stat, ai in zip(statistical_result["quantities"], ai_result.get("quantities", statistical_result["quantities"]))
            ],
            "method": "hybrid",
            "confidence": "Medium"
        }
    
    # Save forecast to database
    forecast_record = Forecast(
        user_id=current_user.id,
        product_id=forecast_request.product_id,
        forecast_data=[
            {
                "forecast_date": date,
                "forecast_qty": qty,
                "confidence_score": 0.8  # Default confidence
            }
            for date, qty in zip(forecast_result["dates"], forecast_result["quantities"])
        ],
        method_used=forecast_result.get("method", forecast_request.method),
        external_factors=external_data
    )
    
    db.add(forecast_record)
    db.commit()
    db.refresh(forecast_record)
    
    # Log usage
    log_usage(
        current_user.id, 
        "forecast_generated", 
        forecast_record.id, 
        {"method": forecast_request.method, "days": forecast_request.forecast_days},
        db
    )
    
    # Generate alerts in background
    background_tasks.add_task(alert_system.generate_alerts, current_user, db)
    
    # Prepare response
    return ForecastResponse(
        forecast_id=forecast_record.id,
        product_id=forecast_request.product_id,
        forecasts=forecast_record.forecast_data,
        method=forecast_result.get("method", forecast_request.method),
        confidence=forecast_result.get("confidence", "Medium"),
        reorder_quantity=forecast_result.get("reorder_quantity"),
        key_factors=forecast_result.get("key_factors"),
        risk_assessment=forecast_result.get("risk_assessment"),
        recommendations=forecast_result.get("recommendations"),
        explanation=forecast_result.get("explanation"),
        created_at=forecast_record.created_at
    )

@app.post("/forecast/scenario")
async def generate_scenario_forecast(
    scenario_request: ScenarioForecastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate what-if scenario forecast"""
    # Similar validation as regular forecast
    if not check_usage_limit(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly forecast limit reached for {current_user.subscription_tier} tier"
        )
    
    product = db.query(Product).filter(
        Product.id == scenario_request.product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get sales data
    sales_data = db.query(SalesData).filter(
        SalesData.product_id == scenario_request.product_id
    ).order_by(SalesData.date).all()
    
    sales_list = [
        {"date": sale.date.strftime("%Y-%m-%d"), "quantity": sale.quantity}
        for sale in sales_data
    ]
    
    # Generate scenario forecast
    forecast_result = await forecasting_engine.generate_scenario_forecast(
        product, sales_list, scenario_request.scenario
    )
    
    # Log usage
    log_usage(
        current_user.id,
        "scenario_forecast_generated",
        scenario_request.product_id,
        {"scenario": scenario_request.scenario},
        db
    )
    
    return {
        "product_id": scenario_request.product_id,
        "scenario": scenario_request.scenario,
        "forecast": forecast_result,
        "disclaimer": "Scenario forecasts are estimates based on hypothetical conditions"
    }

@app.get("/alerts")
async def get_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user alerts"""
    alerts = alert_system.get_user_alerts(current_user.id, db, unread_only)
    
    return {
        "alerts": [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "is_read": alert.is_read,
                "is_resolved": alert.is_resolved,
                "created_at": alert.created_at
            }
            for alert in alerts
        ]
    }

@app.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark alert as read"""
    alert_system.mark_alert_read(alert_id, current_user.id, db)
    return {"message": "Alert marked as read"}

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve alert"""
    alert_system.resolve_alert(alert_id, current_user.id, db)
    return {"message": "Alert resolved"}

@app.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary"""
    # Get summary statistics
    total_products = db.query(func.count(Product.id)).filter(Product.user_id == current_user.id).scalar()
    
    total_forecasts = db.query(func.count(Forecast.id)).filter(Forecast.user_id == current_user.id).scalar()
    
    unread_alerts = db.query(func.count(Alert.id)).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).scalar()
    
    # Recent forecasts
    recent_forecasts = db.query(Forecast).filter(
        Forecast.user_id == current_user.id
    ).order_by(desc(Forecast.created_at)).limit(5).all()
    
    return {
        "summary": {
            "total_products": total_products,
            "total_forecasts": total_forecasts,
            "unread_alerts": unread_alerts,
            "subscription_tier": current_user.subscription_tier
        },
        "recent_forecasts": [
            {
                "id": forecast.id,
                "product_id": forecast.product_id,
                "method": forecast.method_used,
                "created_at": forecast.created_at
            }
            for forecast in recent_forecasts
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
