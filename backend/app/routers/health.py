from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from backend.app.db.session import get_db
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check the health of the API and its dependencies."""
    health_status = {
        "status": "healthy",
        "api": "ok",
        "database": "ok",
        "redis": "ok"
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Sentiment Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }