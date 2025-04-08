from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

class Goal(BaseModel):
    type: str
    target_amount: float
    timeline: int

class NewsArticleSummary(BaseModel):
    published_at: datetime
    summary: str 
    source_url: str

class NewsArticle(BaseModel):
    title: str
    summary: str
    url: str
    publishedAt: str
    source: str

class NewsArticleCollection(BaseModel):
    articles: List[NewsArticle]
    fetch_timestamp: datetime = Field(default_factory=datetime.now)

class UserProfile(BaseModel):
    age: int
    income: float
    dependents: int
    investment_horizon: int
    existing_investments: List[Dict[str, Any]]
    risk_tolerance: str
    goals: List[Dict[str, Any]]

    class Config:
        arbitrary_types_allowed = True

class RiskAnalysis(BaseModel):
    risk_score: float
    risk_category: str
    key_factors: List[str]
    recommendations: List[str]

class InvestmentRecommendation(BaseModel):
    asset_allocation: Dict[str, float]
    specific_recommendations: List[Dict[str, Any]]
    market_news: List[NewsArticle]

class MarketAnalysis(BaseModel):
    market_trends: List[str]
    key_insights: List[str]
    impact_analysis: List[str]

class WealthManagementResponse(BaseModel):
    risk_analysis: RiskAnalysis
    market_analysis: MarketAnalysis
    recommendations: InvestmentRecommendation
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatResponse(BaseModel):
    """Response model for financial chat service"""
    answer: str
    sources: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now) 