#!/usr/bin/env python3
"""
Aqlify Universal Forecasting Platform - Production Demo
Run this to see a complete demo of the forecasting platform
"""

import asyncio
import json
from datetime import datetime, timedelta
import uvicorn
from main_v3 import app

def create_demo_data():
    """Generate demo data for testing"""
    
    # Demo sales data for a coffee shop
    base_date = datetime(2025, 1, 1)
    demo_sales = []
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Simulate realistic coffee sales with weekend patterns
        base_quantity = 50
        if date.weekday() >= 5:  # Weekend
            base_quantity = 75
        
        # Add some randomness
        import random
        quantity = base_quantity + random.randint(-10, 15)
        
        demo_sales.append({
            "date": date.strftime("%Y-%m-%d"),
            "quantity": max(1, quantity),
            "revenue": quantity * 4.50,  # $4.50 per coffee
            "channel": "retail",
            "region": "Muscat"
        })
    
    return demo_sales

def print_platform_info():
    """Print information about the platform"""
    print("🚀 " + "="*60)
    print("   AQLIFY UNIVERSAL FORECASTING PLATFORM")
    print("   Production-Ready SaaS Solution")
    print("="*62)
    print()
    print("✨ FEATURES:")
    print("   • Multi-tenant SaaS architecture")
    print("   • AI-powered demand forecasting")
    print("   • Real-time business alerts") 
    print("   • External data integration")
    print("   • Scenario planning & what-if analysis")
    print("   • Multi-algorithm ensemble forecasting")
    print("   • Subscription tier management")
    print("   • Comprehensive API documentation")
    print()
    print("🛠️  TECHNOLOGY STACK:")
    print("   • FastAPI + Python 3.11")
    print("   • PostgreSQL + SQLAlchemy ORM")
    print("   • Redis caching")
    print("   • OpenAI GPT-4 integration")
    print("   • JWT authentication")
    print("   • Docker deployment")
    print()
    print("📊 BUSINESS TIERS:")
    print("   • FREE: 100 forecasts/month")
    print("   • PREMIUM: 1,000 forecasts/month") 
    print("   • ENTERPRISE: 10,000 forecasts/month")
    print()
    print("🌐 API ENDPOINTS:")
    print("   • POST /auth/register - Register business")
    print("   • POST /auth/login - User authentication")
    print("   • POST /products - Create products")
    print("   • POST /sales-data - Upload sales data")
    print("   • POST /forecast - Generate AI forecasts")
    print("   • POST /forecast/scenario - Scenario planning")
    print("   • GET /alerts - Business intelligence alerts")
    print("   • GET /dashboard - Business dashboard")
    print()
    print("📖 DOCUMENTATION:")
    print("   • Interactive API: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    print()
    print("🔧 DEMO DATA:")
    demo_data = create_demo_data()
    print(f"   • Generated {len(demo_data)} days of sample sales data")
    print(f"   • Sample: {demo_data[0]}")
    print()
    print("🚀 Starting server on http://localhost:8000")
    print("="*62)

async def run_demo():
    """Run a quick demo of the platform capabilities"""
    print_platform_info()
    print("\n🎯 QUICK DEMO:")
    print("1. Platform supports any business type")
    print("2. Multi-algorithm forecasting engine")
    print("3. Real-time external data integration")
    print("4. Intelligent business alerts")
    print("5. Scalable SaaS architecture")
    print("\nReady for production deployment! 🎉")

if __name__ == "__main__":
    print("\n" + "🎯 AQLIFY - UNIVERSAL BUSINESS FORECASTING PLATFORM" + "\n")
    
    # Run demo
    asyncio.run(run_demo())
    
    print("\nStarting FastAPI server...")
    print("Visit http://localhost:8000/docs for complete API documentation\n")
    
    # Start the server
    uvicorn.run(
        "main_v3:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
