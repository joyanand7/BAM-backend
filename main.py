from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import router as api_router

app = FastAPI(
    title="Wealth Management API",
    description="API for wealth management, financial chat, and news services",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the Wealth Management API"} 