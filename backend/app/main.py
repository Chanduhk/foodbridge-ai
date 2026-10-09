from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.donation import router as donation_router
from app.routers.recipient import router as recipient_router
from app.routers.matching import router as matching_router
from app.routers.allocation import router as allocation_router
from app.routers.delivery import router as delivery_router
from app.routers.ml import router as ml_router
from app.routers.analytics import router as analytics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FoodBridge AI — Connecting surplus-food donors, verified recipient organizations, and volunteers for UN SDG 2 (Zero Hunger).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
origins = settings.BACKEND_CORS_ORIGINS if isinstance(settings.BACKEND_CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(donation_router, prefix=settings.API_V1_STR)
app.include_router(recipient_router, prefix=settings.API_V1_STR)
app.include_router(matching_router, prefix=settings.API_V1_STR)
app.include_router(allocation_router, prefix=settings.API_V1_STR)
app.include_router(delivery_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])






@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs"
    }
