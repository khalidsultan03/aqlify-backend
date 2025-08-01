"""
Example usage of the Aqlify Universal Forecasting Platform
This demonstrates how businesses can integrate with the API
"""

import requests
import json
from datetime import datetime, timedelta

class AqlifyClient:
    """Client SDK for Aqlify Forecasting Platform"""
    
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def register_business(self, email, password, company_name, industry=None, country=None):
        """Register a new business on the platform"""
        response = self.session.post(f"{self.base_url}/auth/register", json={
            "email": email,
            "password": password,
            "company_name": company_name,
            "industry": industry,
            "country": country
        })
        
        if response.status_code == 200:
            data = response.json()
            self.api_key = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            return data
        else:
            raise Exception(f"Registration failed: {response.text}")
    
    def login(self, email, password):
        """Login to existing account"""
        response = self.session.post(f"{self.base_url}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.api_key = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            return data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def create_product(self, name, category=None, sku=None, unit_price=None, 
                      supplier=None, lead_time_days=7, safety_stock_days=7):
        """Create a new product"""
        response = self.session.post(f"{self.base_url}/products", json={
            "name": name,
            "category": category,
            "sku": sku,
            "unit_price": unit_price,
            "supplier": supplier,
            "lead_time_days": lead_time_days,
            "safety_stock_days": safety_stock_days
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Product creation failed: {response.text}")
    
    def upload_sales_data(self, product_id, sales_data):
        """Upload historical sales data"""
        response = self.session.post(f"{self.base_url}/sales-data", json={
            "product_id": product_id,
            "sales_data": sales_data
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Sales data upload failed: {response.text}")
    
    def generate_forecast(self, product_id, forecast_days=30, method="ai", 
                         include_external_data=True, user_notes=None):
        """Generate demand forecast"""
        response = self.session.post(f"{self.base_url}/forecast", json={
            "product_id": product_id,
            "forecast_days": forecast_days,
            "method": method,
            "include_external_data": include_external_data,
            "user_notes": user_notes
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Forecast generation failed: {response.text}")
    
    def scenario_forecast(self, product_id, scenario, forecast_days=30):
        """Generate what-if scenario forecast"""
        response = self.session.post(f"{self.base_url}/forecast/scenario", json={
            "product_id": product_id,
            "forecast_days": forecast_days,
            "scenario": scenario
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Scenario forecast failed: {response.text}")
    
    def get_alerts(self, unread_only=False):
        """Get business alerts"""
        params = {"unread_only": unread_only} if unread_only else {}
        response = self.session.get(f"{self.base_url}/alerts", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get alerts: {response.text}")
    
    def get_dashboard(self):
        """Get business dashboard summary"""
        response = self.session.get(f"{self.base_url}/dashboard")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get dashboard: {response.text}")

def demo_coffee_shop():
    """Demo: Coffee shop using Aqlify for demand forecasting"""
    print("☕ COFFEE SHOP DEMO")
    print("=" * 50)
    
    # Initialize client
    client = AqlifyClient()
    
    # Register business
    print("1. Registering coffee shop business...")
    user_data = client.register_business(
        email="owner@bestcoffee.com",
        password="securepassword123",
        company_name="Best Coffee Shop",
        industry="Food & Beverage",
        country="Oman"
    )
    print(f"✅ Registered: {user_data['user']['company_name']}")
    
    # Create products
    print("\n2. Adding coffee products...")
    
    products = [
        {
            "name": "Premium Arabica Coffee",
            "category": "Hot Beverages",
            "sku": "COFFEE-001",
            "unit_price": 4.50,
            "supplier": "Local Roasters",
            "lead_time_days": 3,
            "safety_stock_days": 7
        },
        {
            "name": "Espresso Shots",
            "category": "Hot Beverages", 
            "sku": "ESP-001",
            "unit_price": 2.75,
            "supplier": "Local Roasters",
            "lead_time_days": 3,
            "safety_stock_days": 5
        }
    ]
    
    created_products = []
    for product_data in products:
        product = client.create_product(**product_data)
        created_products.append(product["product"])
        print(f"✅ Created: {product_data['name']}")
    
    # Generate sample sales data
    print("\n3. Uploading historical sales data...")
    
    def generate_coffee_sales(days=30):
        base_date = datetime.now() - timedelta(days=days)
        sales = []
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            
            # Coffee shop patterns: higher on weekends, weather dependent
            base_quantity = 45
            if date.weekday() >= 5:  # Weekend
                base_quantity = 65
            if date.weekday() == 0:  # Monday blues need more coffee
                base_quantity = 55
            
            # Add realistic variation
            import random
            quantity = base_quantity + random.randint(-8, 12)
            
            sales.append({
                "date": date.strftime("%Y-%m-%d"),
                "quantity": max(1, quantity),
                "revenue": quantity * 4.50,
                "channel": "retail",
                "region": "Muscat"
            })
        
        return sales
    
    for product in created_products:
        sales_data = generate_coffee_sales(30)
        result = client.upload_sales_data(product["id"], sales_data)
        print(f"✅ Uploaded {len(sales_data)} days of sales for {product['name']}")
    
    # Generate forecasts
    print("\n4. Generating AI-powered forecasts...")
    
    for product in created_products:
        forecast = client.generate_forecast(
            product_id=product["id"],
            forecast_days=14,
            method="ai",
            include_external_data=True,
            user_notes="Expecting increased demand due to new marketing campaign and upcoming weekend events"
        )
        
        print(f"\n📊 Forecast for {product['name']}:")
        print(f"   Method: {forecast['method']}")
        print(f"   Confidence: {forecast['confidence']}")
        if forecast.get('reorder_quantity'):
            print(f"   Recommended reorder: {forecast['reorder_quantity']} units")
        
        # Show first 5 days of forecast
        print("   Next 5 days forecast:")
        for i, day_forecast in enumerate(forecast['forecasts'][:5]):
            print(f"     {day_forecast['forecast_date']}: {day_forecast['forecast_qty']} units")
    
    # Scenario planning
    print("\n5. Running scenario analysis...")
    
    scenarios = [
        {
            "name": "Rainy Weather + Economic Growth",
            "params": {
                "demand_change_percent": 15,
                "weather_impact": "rain", 
                "economic_impact": "growth"
            }
        },
        {
            "name": "Holiday Season Boost",
            "params": {
                "demand_change_percent": 35,
                "weather_impact": "normal",
                "economic_impact": "stable"
            }
        }
    ]
    
    for scenario in scenarios:
        scenario_result = client.scenario_forecast(
            product_id=created_products[0]["id"],
            scenario=scenario["params"],
            forecast_days=7
        )
        
        total_forecast = sum(day["forecast_qty"] for day in scenario_result["forecast"]["quantities"])
        print(f"   {scenario['name']}: {total_forecast} units over 7 days")
    
    # Check alerts
    print("\n6. Checking business alerts...")
    alerts = client.get_alerts()
    
    if alerts["alerts"]:
        for alert in alerts["alerts"][:3]:  # Show first 3 alerts
            print(f"   🚨 {alert['severity'].upper()}: {alert['message']}")
    else:
        print("   ✅ No alerts - business is running smoothly!")
    
    # Dashboard summary
    print("\n7. Business Dashboard Summary:")
    dashboard = client.get_dashboard()
    summary = dashboard["summary"]
    
    print(f"   📦 Total Products: {summary['total_products']}")
    print(f"   📈 Total Forecasts: {summary['total_forecasts']}")
    print(f"   🔔 Unread Alerts: {summary['unread_alerts']}")
    print(f"   💎 Subscription: {summary['subscription_tier'].upper()}")
    
    print("\n" + "=" * 50)
    print("✅ Coffee shop is now using AI-powered demand forecasting!")
    print("🚀 Ready to optimize inventory and reduce waste!")

def demo_retail_store():
    """Demo: Retail store managing multiple product categories"""
    print("\n🏪 RETAIL STORE DEMO")
    print("=" * 50)
    
    client = AqlifyClient()
    
    # Register retail business
    user_data = client.register_business(
        email="manager@retailstore.com", 
        password="retailpass123",
        company_name="Smart Retail Store",
        industry="Retail",
        country="UAE"
    )
    print(f"✅ Registered: {user_data['user']['company_name']}")
    
    # Create diverse product portfolio
    retail_products = [
        {"name": "Wireless Headphones", "category": "Electronics", "unit_price": 89.99, "lead_time_days": 14},
        {"name": "Premium T-Shirts", "category": "Clothing", "unit_price": 25.99, "lead_time_days": 7},
        {"name": "Organic Face Cream", "category": "Beauty", "unit_price": 45.00, "lead_time_days": 10},
        {"name": "Protein Powder", "category": "Health", "unit_price": 75.99, "lead_time_days": 5}
    ]
    
    print(f"\n📦 Creating {len(retail_products)} products across different categories...")
    
    created_products = []
    for product_data in retail_products:
        product = client.create_product(**product_data)
        created_products.append(product["product"])
        print(f"   ✅ {product_data['name']} ({product_data['category']})")
    
    print(f"\n🏪 Retail store now has {len(created_products)} products ready for AI forecasting!")

if __name__ == "__main__":
    print("🎯 AQLIFY UNIVERSAL FORECASTING PLATFORM")
    print("   Real-world Business Demos")
    print("=" * 60)
    
    try:
        # Run coffee shop demo
        demo_coffee_shop()
        
        # Run retail store demo  
        demo_retail_store()
        
        print("\n" + "=" * 60)
        print("🎉 DEMOS COMPLETE!")
        print("💡 The platform works for ANY business type:")
        print("   • Restaurants & Cafes")
        print("   • Retail & E-commerce") 
        print("   • Manufacturing")
        print("   • Healthcare & Pharmacy")
        print("   • Automotive")
        print("   • Agriculture")
        print("   • Technology")
        print("   • And many more!")
        print("\n🚀 Ready for production deployment!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure the Aqlify server is running on http://localhost:8000")
        print("   Run: python run_demo.py")
