import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from config import settings
from database import ExternalData

class ExternalDataCollector:
    """Collects external data from various APIs to enhance forecasting"""
    
    def __init__(self):
        self.weather_api_key = settings.WEATHER_API_KEY
        self.news_api_key = settings.NEWS_API_KEY
    
    async def collect_weather_data(self, region: str, days: int = 7) -> Dict:
        """Collect weather forecast data"""
        if not self.weather_api_key:
            return {}
        
        url = f"http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": self.weather_api_key,
            "q": region,
            "days": min(days, 10),  # API limit
            "aqi": "no",
            "alerts": "yes"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_weather_data(data)
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return {}
    
    def _process_weather_data(self, raw_data: Dict) -> Dict:
        """Process raw weather data into useful features"""
        processed = {
            "temperature_avg": [],
            "precipitation": [],
            "humidity": [],
            "extreme_weather_alerts": []
        }
        
        if "forecast" in raw_data:
            for day in raw_data["forecast"]["forecastday"]:
                day_data = day["day"]
                processed["temperature_avg"].append(day_data.get("avgtemp_c", 0))
                processed["precipitation"].append(day_data.get("totalprecip_mm", 0))
                processed["humidity"].append(day_data.get("avghumidity", 0))
        
        if "alerts" in raw_data:
            processed["extreme_weather_alerts"] = [
                alert["headline"] for alert in raw_data["alerts"]["alert"]
            ]
        
        return processed
    
    async def collect_economic_indicators(self, country: str = "OM") -> Dict:
        """Collect economic indicators (mock implementation)"""
        # In production, integrate with APIs like Trading Economics, World Bank, etc.
        return {
            "gdp_growth": 2.1,
            "inflation_rate": 1.8,
            "unemployment_rate": 3.2,
            "oil_price_change_7d": 2.5,
            "currency_exchange_rate": 0.385  # OMR to USD
        }
    
    async def collect_news_sentiment(self, query: str, days: int = 7) -> Dict:
        """Collect news sentiment analysis"""
        if not self.news_api_key:
            return {"sentiment_score": 0.0, "news_count": 0}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": self.news_api_key,
            "q": query,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 50
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._analyze_news_sentiment(data.get("articles", []))
        except Exception as e:
            print(f"News API error: {e}")
        
        return {"sentiment_score": 0.0, "news_count": 0}
    
    def _analyze_news_sentiment(self, articles: List[Dict]) -> Dict:
        """Simple sentiment analysis of news articles"""
        positive_words = ["growth", "increase", "boost", "positive", "strong", "recovery", "surge"]
        negative_words = ["decline", "decrease", "drop", "negative", "weak", "crisis", "fall"]
        
        total_score = 0
        total_articles = len(articles)
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                total_score += 1
            elif negative_count > positive_count:
                total_score -= 1
        
        sentiment_score = total_score / max(total_articles, 1)
        
        return {
            "sentiment_score": sentiment_score,
            "news_count": total_articles,
            "sample_headlines": [article.get("title", "") for article in articles[:3]]
        }
    
    async def collect_all_external_data(self, region: str, product_category: str, db: Session):
        """Collect all external data and store in database"""
        tasks = [
            self.collect_weather_data(region),
            self.collect_economic_indicators(),
            self.collect_news_sentiment(product_category)
        ]
        
        weather_data, economic_data, news_data = await asyncio.gather(*tasks)
        
        # Store in database
        current_date = datetime.now()
        
        external_data_entries = [
            ExternalData(
                data_type="weather",
                region=region,
                date=current_date,
                data=weather_data
            ),
            ExternalData(
                data_type="economic",
                region=region,
                date=current_date,
                data=economic_data
            ),
            ExternalData(
                data_type="news",
                region=region,
                date=current_date,
                data=news_data
            )
        ]
        
        for entry in external_data_entries:
            db.add(entry)
        
        db.commit()
        
        return {
            "weather": weather_data,
            "economic": economic_data,
            "news": news_data
        }

# Global instance
external_data_collector = ExternalDataCollector()
