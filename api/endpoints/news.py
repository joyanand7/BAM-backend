from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from app.services.news_service import fetch_financial_news
from app.models.schemas import NewsArticleCollection

router = APIRouter()

@router.get("/latest", response_model=NewsArticleCollection)
async def get_latest_news():
    """Get the latest financial news"""
    try:
        # Fetch news using the news service
        news_data = await fetch_financial_news()
        
        # Parse the JSON string into a NewsArticleCollection
        return NewsArticleCollection.parse_raw(news_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 