import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session

from config import settings
from database import SalesData, Product, ExternalData, Forecast
from external_data import external_data_collector

class AdvancedForecastingEngine:
    """Advanced forecasting engine with multiple algorithms and AI integration"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    def calculate_statistical_forecast(self, sales_data: List[Dict], days: int = 30) -> Dict:
        """Statistical forecasting using multiple methods"""
        quantities = [item["quantity"] for item in sales_data]
        dates = [datetime.strptime(item["date"], "%Y-%m-%d") for item in sales_data]
        
        # Simple Moving Average
        sma_forecast = self._simple_moving_average(quantities, days)
        
        # Exponential Smoothing
        ema_forecast = self._exponential_smoothing(quantities, days)
        
        # Linear Trend
        trend_forecast = self._linear_trend(quantities, days)
        
        # Seasonal decomposition (if enough data)
        seasonal_forecast = self._seasonal_forecast(quantities, days) if len(quantities) >= 28 else ema_forecast
        
        # Ensemble - weighted average of methods
        ensemble_weights = [0.2, 0.3, 0.2, 0.3]  # SMA, EMA, Trend, Seasonal
        
        forecast_dates = []
        forecast_quantities = []
        
        last_date = max(dates)
        for i in range(days):
            forecast_date = last_date + timedelta(days=i+1)
            forecast_dates.append(forecast_date.strftime("%Y-%m-%d"))
            
            # Weighted ensemble
            ensemble_qty = (
                ensemble_weights[0] * sma_forecast[i] +
                ensemble_weights[1] * ema_forecast[i] +
                ensemble_weights[2] * trend_forecast[i] +
                ensemble_weights[3] * seasonal_forecast[i]
            )
            
            forecast_quantities.append(max(0, int(round(ensemble_qty))))
        
        return {
            "dates": forecast_dates,
            "quantities": forecast_quantities,
            "method": "statistical_ensemble",
            "confidence": self._calculate_confidence(quantities, forecast_quantities[:7])
        }
    
    def _simple_moving_average(self, data: List[float], forecast_days: int, window: int = 7) -> List[float]:
        """Simple moving average forecast"""
        if len(data) < window:
            window = len(data)
        
        avg = sum(data[-window:]) / window
        return [avg] * forecast_days
    
    def _exponential_smoothing(self, data: List[float], forecast_days: int, alpha: float = 0.3) -> List[float]:
        """Exponential smoothing forecast"""
        if not data:
            return [0] * forecast_days
        
        smoothed = [data[0]]
        for i in range(1, len(data)):
            smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[-1])
        
        last_smoothed = smoothed[-1]
        return [last_smoothed] * forecast_days
    
    def _linear_trend(self, data: List[float], forecast_days: int) -> List[float]:
        """Linear trend extrapolation"""
        if len(data) < 2:
            return [data[0] if data else 0] * forecast_days
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Linear regression
        A = np.vstack([x, np.ones(len(x))]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        
        forecast = []
        for i in range(forecast_days):
            future_x = len(data) + i
            predicted = slope * future_x + intercept
            forecast.append(max(0, predicted))
        
        return forecast
    
    def _seasonal_forecast(self, data: List[float], forecast_days: int) -> List[float]:
        """Simple seasonal forecast assuming weekly patterns"""
        if len(data) < 14:
            return self._exponential_smoothing(data, forecast_days)
        
        # Assume 7-day weekly seasonality
        weekly_pattern = []
        for day in range(7):
            day_values = [data[i] for i in range(day, len(data), 7) if i < len(data)]
            weekly_pattern.append(sum(day_values) / len(day_values) if day_values else 0)
        
        forecast = []
        for i in range(forecast_days):
            seasonal_factor = weekly_pattern[i % 7]
            base_trend = sum(data[-7:]) / 7  # Recent average
            forecast.append(max(0, base_trend * (seasonal_factor / (sum(weekly_pattern) / 7))))
        
        return forecast
    
    def _calculate_confidence(self, historical: List[float], forecast_sample: List[float]) -> str:
        """Calculate forecast confidence based on historical variance"""
        if len(historical) < 7:
            return "Low"
        
        recent_variance = np.var(historical[-14:])
        historical_mean = np.mean(historical[-14:])
        
        if recent_variance / (historical_mean + 1) < 0.1:
            return "High"
        elif recent_variance / (historical_mean + 1) < 0.3:
            return "Medium"
        else:
            return "Low"
    
    async def generate_ai_forecast(self, product: Product, sales_data: List[Dict], 
                                 external_data: Dict, user_notes: str = None) -> Dict:
        """Generate AI-powered forecast using OpenAI"""
        if not self.openai_client:
            return self.calculate_statistical_forecast(sales_data)
        
        # Prepare context
        sales_summary = self._prepare_sales_summary(sales_data)
        external_summary = self._prepare_external_summary(external_data)
        
        system_prompt = """You are an expert demand forecasting AI with deep knowledge of:
- Statistical forecasting methods
- Seasonal patterns and trends
- External factor impacts (weather, economics, news)
- Industry-specific demand drivers
- Regional market dynamics

Analyze all provided data and generate accurate demand forecasts."""

        user_prompt = f"""
Product Information:
- Name: {product.name}
- Category: {product.category}
- Lead Time: {product.lead_time_days} days
- Safety Stock: {product.safety_stock_days} days

Sales Data Analysis:
{sales_summary}

External Factors:
{external_summary}

{"User Notes: " + user_notes if user_notes else ""}

Please provide a 30-day demand forecast considering:
1. Historical sales patterns and trends
2. Seasonal effects and weekly patterns
3. External factors (weather, economic, news sentiment)
4. Product category characteristics
5. Any anomalies or special events

Respond with JSON in this exact format:
{{
  "forecasts": [
    {{"forecast_date": "YYYY-MM-DD", "forecast_qty": integer, "confidence_score": float}}
  ],
  "reorder_quantity": integer,
  "confidence_level": "High|Medium|Low",
  "key_factors": ["factor1", "factor2"],
  "risk_assessment": "Low|Medium|High",
  "recommendations": ["recommendation1", "recommendation2"],
  "explanation": "detailed explanation of forecast reasoning"
}}
"""

        try:
            response = await self._call_openai(system_prompt, user_prompt)
            forecast_data = json.loads(response)
            forecast_data["method"] = "ai_enhanced"
            return forecast_data
        except Exception as e:
            print(f"AI forecast failed: {e}")
            # Fallback to statistical
            return self.calculate_statistical_forecast(sales_data)
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API asynchronously"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _prepare_sales_summary(self, sales_data: List[Dict]) -> str:
        """Prepare sales data summary for AI analysis"""
        quantities = [item["quantity"] for item in sales_data]
        
        total_sales = sum(quantities)
        avg_daily = total_sales / len(quantities)
        max_day = max(quantities)
        min_day = min(quantities)
        
        # Trend analysis
        recent_7 = quantities[-7:] if len(quantities) >= 7 else quantities
        previous_7 = quantities[-14:-7] if len(quantities) >= 14 else []
        
        trend = "stable"
        if previous_7:
            recent_avg = sum(recent_7) / len(recent_7)
            previous_avg = sum(previous_7) / len(previous_7)
            change = (recent_avg - previous_avg) / previous_avg
            
            if change > 0.1:
                trend = "increasing"
            elif change < -0.1:
                trend = "decreasing"
        
        return f"""
Total sales ({len(quantities)} days): {total_sales}
Daily average: {avg_daily:.1f}
Range: {min_day} - {max_day}
Recent trend: {trend}
Last 7 days: {recent_7}
Variance: {np.var(quantities):.2f}
"""
    
    def _prepare_external_summary(self, external_data: Dict) -> str:
        """Prepare external data summary for AI analysis"""
        summary = []
        
        if "weather" in external_data and external_data["weather"]:
            weather = external_data["weather"]
            avg_temp = np.mean(weather.get("temperature_avg", []))
            total_precip = sum(weather.get("precipitation", []))
            summary.append(f"Weather: Avg temp {avg_temp:.1f}°C, Precipitation {total_precip}mm")
            
            if weather.get("extreme_weather_alerts"):
                summary.append(f"Weather alerts: {', '.join(weather['extreme_weather_alerts'])}")
        
        if "economic" in external_data and external_data["economic"]:
            econ = external_data["economic"]
            summary.append(f"Economic: GDP growth {econ.get('gdp_growth', 0)}%, Inflation {econ.get('inflation_rate', 0)}%")
        
        if "news" in external_data and external_data["news"]:
            news = external_data["news"]
            sentiment = news.get("sentiment_score", 0)
            sentiment_text = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
            summary.append(f"News sentiment: {sentiment_text} ({sentiment:.2f})")
        
        return "\n".join(summary) if summary else "No external data available"
    
    async def generate_scenario_forecast(self, product: Product, sales_data: List[Dict], 
                                       scenario: Dict) -> Dict:
        """Generate forecast for what-if scenarios"""
        base_forecast = self.calculate_statistical_forecast(sales_data)
        
        # Apply scenario adjustments
        adjustment_factor = 1.0
        
        if scenario.get("demand_change_percent"):
            adjustment_factor *= (1 + scenario["demand_change_percent"] / 100)
        
        if scenario.get("weather_impact"):
            # Simple weather impact model
            weather_multiplier = {
                "extreme_heat": 0.8,
                "rain": 1.2,
                "normal": 1.0
            }
            adjustment_factor *= weather_multiplier.get(scenario["weather_impact"], 1.0)
        
        if scenario.get("economic_impact"):
            # Economic impact on demand
            econ_multiplier = {
                "recession": 0.7,
                "growth": 1.3,
                "stable": 1.0
            }
            adjustment_factor *= econ_multiplier.get(scenario["economic_impact"], 1.0)
        
        # Adjust forecast quantities
        adjusted_quantities = [
            max(0, int(qty * adjustment_factor)) 
            for qty in base_forecast["quantities"]
        ]
        
        return {
            "dates": base_forecast["dates"],
            "quantities": adjusted_quantities,
            "method": "scenario_analysis",
            "scenario": scenario,
            "adjustment_factor": adjustment_factor,
            "confidence": "Medium"  # Scenarios are inherently less certain
        }

# Global instance
forecasting_engine = AdvancedForecastingEngine()
