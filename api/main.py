from fastapi import APIRouter
from .endpoints.wealth import router as wealth_router
from .endpoints.financial_chat import router as financial_chat_router
from .endpoints.news import router as news_router

# Create the main API router
router = APIRouter()

# Include wealth management routes
router.include_router(
    wealth_router,
    prefix="/wealth",
    tags=["wealth"]
)

# Include financial chat routes
router.include_router(
    financial_chat_router,
    prefix="/financial",
    tags=["financial-chat"]
)

# Include news routes
router.include_router(
    news_router,
    prefix="/news",
    tags=["news"]
) 