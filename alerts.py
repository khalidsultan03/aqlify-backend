from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database import Alert, User, Product, SalesData, Forecast

class AlertSystem:
    """Real-time alert system for demand anomalies and business insights"""
    
    def __init__(self):
        self.alert_rules = {
            "stockout_risk": self._check_stockout_risk,
            "unusual_demand": self._check_unusual_demand,
            "forecast_accuracy": self._check_forecast_accuracy,
            "seasonal_anomaly": self._check_seasonal_anomaly,
            "supply_chain_risk": self._check_supply_chain_risk
        }
    
    def generate_alerts(self, user: User, db: Session) -> List[Dict]:
        """Generate all alerts for a user"""
        alerts = []
        
        # Get user's products
        products = db.query(Product).filter(Product.user_id == user.id).all()
        
        for product in products:
            for alert_type, check_function in self.alert_rules.items():
                try:
                    alert = check_function(product, db)
                    if alert:
                        alerts.append(alert)
                        self._save_alert(user.id, product.id, alert, db)
                except Exception as e:
                    print(f"Error checking {alert_type} for product {product.id}: {e}")
        
        return alerts
    
    def _check_stockout_risk(self, product: Product, db: Session) -> Dict:
        """Check for potential stockout based on recent sales and lead time"""
        # Get recent sales data
        recent_sales = db.query(SalesData).filter(
            SalesData.product_id == product.id,
            SalesData.date >= datetime.now() - timedelta(days=7)
        ).all()
        
        if not recent_sales:
            return None
        
        daily_avg = sum(sale.quantity for sale in recent_sales) / len(recent_sales)
        total_lead_time = product.lead_time_days + product.safety_stock_days
        required_stock = daily_avg * total_lead_time
        
        # Get current stock level (assuming last sales data represents current stock)
        # In production, integrate with inventory management system
        current_sales_trend = sum(sale.quantity for sale in recent_sales[-3:]) / 3
        
        if current_sales_trend > daily_avg * 1.5 and required_stock > daily_avg * 7:
            return {
                "type": "stockout_risk",
                "severity": "high",
                "message": f"High stockout risk for {product.name}. Current demand spike detected.",
                "data": {
                    "daily_average": daily_avg,
                    "required_stock": required_stock,
                    "current_trend": current_sales_trend
                }
            }
        
        return None
    
    def _check_unusual_demand(self, product: Product, db: Session) -> Dict:
        """Detect unusual demand patterns"""
        # Get 30 days of sales data
        sales_data = db.query(SalesData).filter(
            SalesData.product_id == product.id,
            SalesData.date >= datetime.now() - timedelta(days=30)
        ).order_by(SalesData.date).all()
        
        if len(sales_data) < 14:
            return None
        
        quantities = [sale.quantity for sale in sales_data]
        recent_7 = quantities[-7:]
        previous_7 = quantities[-14:-7] if len(quantities) >= 14 else []
        
        if not previous_7:
            return None
        
        recent_avg = sum(recent_7) / len(recent_7)
        previous_avg = sum(previous_7) / len(previous_7)
        
        # Check for significant changes
        if previous_avg > 0:
            change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
            
            if change_percent > 50:
                return {
                    "type": "unusual_demand",
                    "severity": "medium",
                    "message": f"Unusual demand spike for {product.name}: {change_percent:.1f}% increase",
                    "data": {
                        "change_percent": change_percent,
                        "recent_average": recent_avg,
                        "previous_average": previous_avg
                    }
                }
            elif change_percent < -50:
                return {
                    "type": "unusual_demand",
                    "severity": "medium",
                    "message": f"Unusual demand drop for {product.name}: {abs(change_percent):.1f}% decrease",
                    "data": {
                        "change_percent": change_percent,
                        "recent_average": recent_avg,
                        "previous_average": previous_avg
                    }
                }
        
        return None
    
    def _check_forecast_accuracy(self, product: Product, db: Session) -> Dict:
        """Check accuracy of recent forecasts"""
        # Get forecasts from 7-30 days ago
        forecast_date_range = (
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=7)
        )
        
        forecasts = db.query(Forecast).filter(
            Forecast.product_id == product.id,
            and_(
                Forecast.created_at >= forecast_date_range[0],
                Forecast.created_at <= forecast_date_range[1]
            )
        ).order_by(desc(Forecast.created_at)).first()
        
        if not forecasts:
            return None
        
        # Get actual sales for the forecasted period
        forecast_data = forecasts.forecast_data
        if not forecast_data or not isinstance(forecast_data, list):
            return None
        
        # Check accuracy (simplified)
        forecast_total = sum(item.get("forecast_qty", 0) for item in forecast_data[:7])
        
        actual_sales = db.query(SalesData).filter(
            SalesData.product_id == product.id,
            SalesData.date >= datetime.now() - timedelta(days=7)
        ).all()
        
        actual_total = sum(sale.quantity for sale in actual_sales)
        
        if forecast_total > 0:
            accuracy = 1 - abs(forecast_total - actual_total) / forecast_total
            
            if accuracy < 0.7:  # Less than 70% accurate
                return {
                    "type": "forecast_accuracy",
                    "severity": "low",
                    "message": f"Low forecast accuracy for {product.name}: {accuracy*100:.1f}%",
                    "data": {
                        "accuracy": accuracy,
                        "forecasted": forecast_total,
                        "actual": actual_total
                    }
                }
        
        return None
    
    def _check_seasonal_anomaly(self, product: Product, db: Session) -> Dict:
        """Check for seasonal anomalies"""
        # Get sales data for the same period last year (if available)
        current_week = datetime.now().isocalendar()[1]
        current_year = datetime.now().year
        
        # Current week sales
        current_week_start = datetime.now() - timedelta(days=7)
        current_sales = db.query(SalesData).filter(
            SalesData.product_id == product.id,
            SalesData.date >= current_week_start
        ).all()
        
        # Same week last year
        last_year_week_start = datetime(current_year - 1, 1, 1) + timedelta(weeks=current_week - 1)
        last_year_week_end = last_year_week_start + timedelta(days=7)
        
        last_year_sales = db.query(SalesData).filter(
            SalesData.product_id == product.id,
            and_(
                SalesData.date >= last_year_week_start,
                SalesData.date <= last_year_week_end
            )
        ).all()
        
        if not current_sales or not last_year_sales:
            return None
        
        current_total = sum(sale.quantity for sale in current_sales)
        last_year_total = sum(sale.quantity for sale in last_year_sales)
        
        if last_year_total > 0:
            seasonal_change = ((current_total - last_year_total) / last_year_total) * 100
            
            if abs(seasonal_change) > 75:  # Significant seasonal deviation
                return {
                    "type": "seasonal_anomaly",
                    "severity": "medium",
                    "message": f"Seasonal anomaly for {product.name}: {seasonal_change:.1f}% vs last year",
                    "data": {
                        "seasonal_change": seasonal_change,
                        "current_week": current_total,
                        "last_year_week": last_year_total
                    }
                }
        
        return None
    
    def _check_supply_chain_risk(self, product: Product, db: Session) -> Dict:
        """Check for supply chain risks (placeholder for external integration)"""
        # In production, integrate with:
        # - Supplier performance APIs
        # - Shipping/logistics APIs
        # - Economic indicators
        # - Geopolitical risk assessments
        
        # Mock implementation
        if product.lead_time_days > 14:  # Long lead time products are riskier
            return {
                "type": "supply_chain_risk",
                "severity": "low",
                "message": f"Monitor supply chain for {product.name}: Long lead time ({product.lead_time_days} days)",
                "data": {
                    "lead_time": product.lead_time_days,
                    "supplier": product.supplier
                }
            }
        
        return None
    
    def _save_alert(self, user_id: str, product_id: str, alert_data: Dict, db: Session):
        """Save alert to database"""
        alert = Alert(
            user_id=user_id,
            product_id=product_id,
            alert_type=alert_data["type"],
            severity=alert_data["severity"],
            message=alert_data["message"]
        )
        
        db.add(alert)
        db.commit()
    
    def get_user_alerts(self, user_id: str, db: Session, unread_only: bool = False) -> List[Alert]:
        """Get alerts for a user"""
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        return query.order_by(desc(Alert.created_at)).limit(50).all()
    
    def mark_alert_read(self, alert_id: str, user_id: str, db: Session):
        """Mark an alert as read"""
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()
        
        if alert:
            alert.is_read = True
            db.commit()
    
    def resolve_alert(self, alert_id: str, user_id: str, db: Session):
        """Mark an alert as resolved"""
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()
        
        if alert:
            alert.is_resolved = True
            alert.is_read = True
            db.commit()

# Global instance
alert_system = AlertSystem()
