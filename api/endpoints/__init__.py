from fastapi import APIRouter
from .wealth import router as wealth_router
from .financial_chat import router as financial_chat_router

router = APIRouter()

router.include_router(
    wealth_router,
    prefix="/wealth",
    tags=["wealth"]
)

router.include_router(
    financial_chat_router,
    prefix="/financial",
    tags=["financial-chat"]
) 