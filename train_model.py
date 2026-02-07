#!/usr/bin/env python3
"""Train a simple sentiment analysis model."""

import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd


def create_sample_data():
    """Create sample training data."""
    # Sample positive and negative texts
    data = {
        'text': [
            # Positive samples
            "I love this product! It's amazing!",
            "This is the best thing ever!",
            "Absolutely wonderful experience!",
            "Great service and quality!",
            "I'm so happy with this purchase!",
            "Excellent work, highly recommend!",
            "Perfect! Exactly what I needed!",
            "Outstanding quality and fast delivery!",
            "Very satisfied with everything!",
            "Fantastic! Will buy again!",
            "I love it! Very good quality!",
            "Impressive results, very pleased!",
            "Superb! Exceeded my expectations!",
            "Wonderful product, great value!",
            "Amazing! Could not be happier!",
            
            # Negative samples
            "This is terrible, very disappointed.",
            "Waste of money, poor quality.",
            "I hate this, it's awful.",
            "Very bad experience, not recommended.",
            "Terrible service, will not return.",
            "Poor quality, broke after one use.",
            "Disappointed with the purchase.",
            "Not worth it, complete waste.",
            "Horrible! Do not buy this!",
            "Very unhappy with this product.",
            "Worst purchase ever made.",
            "Terrible quality and service.",
            "Awful experience, avoid this.",
            "Very disappointed, poor value.",
            "Bad product, waste of time."
        ],
        'sentiment': [1] * 15 + [0] * 15  # 1 = positive, 0 = negative
    }
    return pd.DataFrame(data)


def train_model():
    """Train the sentiment analysis model."""
    print("Creating sample training data...")
    df = create_sample_data()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], 
        df['sentiment'], 
        test_size=0.2, 
        random_state=42
    )
    
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # Create pipeline
    model = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf', MultinomialNB())
    ])
    
    print("\nTraining model...")
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['negative', 'positive']))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/sentiment_model.pkl'
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Test predictions
    print("\nTest predictions:")
    test_texts = [
        "This is great!",
        "This is terrible!",
        "I love it!",
        "I hate it!"
    ]
    
    for text in test_texts:
        prediction = model.predict([text])[0]
        probabilities = model.predict_proba([text])[0]
        sentiment = "positive" if prediction == 1 else "negative"
        confidence = max(probabilities)
        print(f"Text: '{text}' -> Sentiment: {sentiment} (confidence: {confidence:.2%})")


if __name__ == "__main__":
    train_model()