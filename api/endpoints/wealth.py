from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ...models.schemas import UserProfile, NewsArticleCollection, WealthManagementResponse
from ...services.wealth_service import get_wealth_management_advice

router = APIRouter()

class WealthAdviceRequest(BaseModel):
    """Request model for wealth management advice"""
    age: int
    income: float
    dependents: int
    investment_horizon: int
    existing_investments: List[Dict[str, Any]]
    risk_tolerance: str
    goals: List[Dict[str, Any]]

@router.post("/advice", response_model=WealthManagementResponse)
async def get_wealth_advice(request: WealthAdviceRequest):
    """
    Get personalized wealth management advice based on user profile.
    
    The advice includes:
    - Risk analysis
    - Market analysis
    - Investment recommendations
    """
    try:
        # Convert request to UserProfile
        user_profile = UserProfile(
            age=request.age,
            income=request.income,
            dependents=request.dependents,
            investment_horizon=request.investment_horizon,
            existing_investments=request.existing_investments,
            risk_tolerance=request.risk_tolerance,
            goals=request.goals
        )
        
        # Create empty news collection (news will be fetched by the service)
        market_news = NewsArticleCollection(articles=[])
        
        return await get_wealth_management_advice(user_profile, market_news)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing wealth management advice: {str(e)}"
        ) 