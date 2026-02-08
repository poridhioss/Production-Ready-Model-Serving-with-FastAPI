from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
import joblib
import time
import os
import uuid
import json

from backend.app.db.models import User, SentimentRequest as DBSentimentRequest, BackgroundTask as DBBackgroundTask
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_active_user

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])

# ML Model
MODEL_PATH = "models/sentiment_model.pkl"
model = None


def load_model():
    """Load the sentiment analysis model."""
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        
        model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000)),
            ('clf', MultinomialNB())
        ])


load_model()


def predict_sentiment(text: str):
    """Predict sentiment of text."""
    if model is None:
        load_model()
    
    try:
        prediction = model.predict([text])[0]
        probabilities = model.predict_proba([text])[0]
        confidence = float(max(probabilities))
        sentiment_map = {0: "negative", 1: "positive"}
        sentiment = sentiment_map.get(prediction, "neutral")
        return sentiment, confidence
    except:
        return "neutral", 0.5


async def process_batch_sentiment(texts: List[str], task_id: str, db: Session):
    """Background task to process batch sentiment analysis."""
    try:
        results = []
        for text in texts:
            sentiment, confidence = predict_sentiment(text)
            results.append({
                "text": text,
                "sentiment": sentiment,
                "confidence": confidence
            })
        
        task = db.query(DBBackgroundTask).filter(
            DBBackgroundTask.task_id == task_id
        ).first()
        if task:
            task.status = "completed"
            task.result = json.dumps(results)
            db.commit()
    except Exception as e:
        task = db.query(DBBackgroundTask).filter(
            DBBackgroundTask.task_id == task_id
        ).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    processing_time: float


class BatchSentimentRequest(BaseModel):
    texts: List[str]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None  # Changed from dict to Any to accept list or dict
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze sentiment of a single text (synchronous)."""
    start_time = time.time()
    
    sentiment, confidence = predict_sentiment(request.text)
    
    processing_time = time.time() - start_time
    
    # Save request to database
    db_request = DBSentimentRequest(
        user_id=current_user.id,
        text=request.text,
        sentiment=sentiment,
        confidence=confidence,
        processing_time=processing_time
    )
    db.add(db_request)
    db.commit()
    
    return SentimentResponse(
        text=request.text,
        sentiment=sentiment,
        confidence=confidence,
        processing_time=processing_time
    )


@router.post("/analyze/batch")
async def analyze_sentiment_batch(
    request: BatchSentimentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze sentiment of multiple texts (asynchronous background task)."""
    task_id = str(uuid.uuid4())
    
    # Create background task record
    db_task = DBBackgroundTask(
        task_id=task_id,
        user_id=current_user.id,
        task_type="batch_sentiment_analysis",
        status="pending"
    )
    db.add(db_task)
    db.commit()
    
    # Add background task
    background_tasks.add_task(process_batch_sentiment, request.texts, task_id, db)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Batch sentiment analysis started. Use /sentiment/task/{task_id} to check status."
    }


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the status of a background task."""
    task = db.query(DBBackgroundTask).filter(
        DBBackgroundTask.task_id == task_id,
        DBBackgroundTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = None
    if task.result:
        result = json.loads(task.result)
    
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        result=result,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/history")
async def get_sentiment_history(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get sentiment analysis history for current user."""
    requests = db.query(DBSentimentRequest).filter(
        DBSentimentRequest.user_id == current_user.id
    ).order_by(DBSentimentRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": req.id,
        "text": req.text,
        "sentiment": req.sentiment,
        "confidence": req.confidence,
        "processing_time": req.processing_time,
        "created_at": req.created_at.isoformat()
    } for req in requests]