"""
API Routes for the ML microservice.
"""

from routes.sentiment import router as sentiment_router
from routes.personality import router as personality_router
from routes.recommendations import router as recommendations_router

__all__ = [
    "sentiment_router",
    "personality_router",
    "recommendations_router",
]
