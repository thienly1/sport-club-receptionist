"""
Sport Club AI Receptionist - Main FastAPI Application
"""

import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db
from .routes import auth, booking, club, conversation, customer, dashboard, notification, vapi

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Voice Receptionist for Sport Clubs - Handles customer service, bookings, and lead generation",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - " f"Status: {response.status_code} - " f"Time: {process_time:.3f}s"
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error occurred"})


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("Starting Sport Club AI Receptionist API...")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

    logger.info(f"API started in {settings.ENVIRONMENT} mode")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Sport Club AI Receptionist API...")


# Include routers
app.include_router(auth.router)
app.include_router(club.router)
app.include_router(customer.router)
app.include_router(booking.router)
app.include_router(conversation.router)
app.include_router(notification.router)
app.include_router(vapi.router)
app.include_router(dashboard.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": time.time()}


# API info endpoint
@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "clubs_management": True,
            "customer_management": True,
            "booking_system": True,
            "ai_assistant": True,
            "notifications": True,
            "vapi_integration": True,
        },
        "endpoints": {
            "clubs": "/clubs",
            "customers": "/customers",
            "bookings": "/bookings",
            "conversations": "/conversations",
            "notifications": "/notifications",
            "vapi_webhook": "/vapi/webhook",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
