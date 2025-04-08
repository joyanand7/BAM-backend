from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...services.financial_chat_service import get_financial_advice
from ...models.schemas import ChatResponse

router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for financial chat"""
    query: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_financial_advisor(request: ChatRequest):
    """
    Chat with a financial advisor AI agent.
    
    The agent can:
    - Answer questions about financial markets
    - Provide investment advice
    - Explain financial concepts
    - Analyze market trends
    - Give personal finance recommendations
    
    The response includes:
    - A detailed answer to your query
    - Sources used for the information
    - Timestamp of the response
    """
    try:
        return await get_financial_advice(request.query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your query: {str(e)}"
        ) 