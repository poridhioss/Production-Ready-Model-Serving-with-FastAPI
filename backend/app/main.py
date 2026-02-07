from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery

from backend.app.core.config import settings
from backend.app.routers import auth, users, protected, sentiment, health

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Celery app for background tasks
celery_app = Celery(
    "sentiment_api",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(protected.router, prefix=settings.API_V1_PREFIX)
app.include_router(sentiment.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Actions to perform on startup."""
    print("Starting Sentiment Analysis API")
    print(f"Environment: {'Development' if settings.DEBUG else 'Production'}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on shutdown."""
    print("Shutting down Sentiment Analysis API")


# Celery tasks
@celery_app.task(name="sentiment_api.analyze_text")
def analyze_text_task(text: str):
    """Celery task for sentiment analysis."""
    from backend.app.routers.sentiment import predict_sentiment
    sentiment, confidence = predict_sentiment(text)
    return {
        "text": text,
        "sentiment": sentiment,
        "confidence": confidence
    }