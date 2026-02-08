"""
Sentiment Analysis Service.
Uses HuggingFace transformers for English and Arabic sentiment analysis.
"""

import hashlib
import structlog
from functools import lru_cache
from typing import Optional

from langdetect import detect, LangDetectException
from transformers import pipeline, Pipeline

from config import get_settings
from models.schemas import SentimentLabel, SentimentResult

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_english_sentiment_model() -> Pipeline:
    """
    Load and cache the English sentiment model.
    Uses lru_cache to ensure model is loaded only once.
    """
    settings = get_settings()
    logger.info("Loading English sentiment model", model=settings.sentiment_model)
    return pipeline(
        "sentiment-analysis",
        model=settings.sentiment_model,
        truncation=True,
        max_length=512,
    )


@lru_cache(maxsize=1)
def get_arabic_sentiment_model() -> Pipeline:
    """
    Load and cache the Arabic sentiment model.
    Uses CAMeL-Lab's Arabic BERT model.
    """
    settings = get_settings()
    logger.info("Loading Arabic sentiment model", model=settings.sentiment_model_arabic)
    return pipeline(
        "sentiment-analysis",
        model=settings.sentiment_model_arabic,
        truncation=True,
        max_length=512,
    )


class SentimentAnalyzer:
    """
    Sentiment analysis service supporting English and Arabic.
    Uses HuggingFace transformers with language auto-detection.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._models_loaded = False

    def _ensure_models_loaded(self) -> None:
        """Ensure models are loaded (lazy loading on first use)."""
        if not self._models_loaded:
            # Trigger model loading
            get_english_sentiment_model()
            try:
                get_arabic_sentiment_model()
            except Exception as e:
                logger.warning("Arabic model not available", error=str(e))
            self._models_loaded = True

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text.

        Args:
            text: Input text

        Returns:
            Language code (e.g., 'en', 'ar')
        """
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            # Default to English if detection fails
            return "en"

    def _normalize_score(self, label: str, score: float) -> tuple[float, SentimentLabel]:
        """
        Normalize model output to a -1 to 1 scale.

        Args:
            label: Model's label output
            score: Model's confidence score

        Returns:
            Tuple of (normalized_score, sentiment_label)
        """
        label_lower = label.lower()

        # Handle different model output formats
        if label_lower in ("positive", "pos", "positive_sentiment", "1"):
            # Positive: score maps to 0 to 1
            normalized = score
            sentiment_label = SentimentLabel.POSITIVE
        elif label_lower in ("negative", "neg", "negative_sentiment", "0"):
            # Negative: score maps to -1 to 0
            normalized = -score
            sentiment_label = SentimentLabel.NEGATIVE
        elif label_lower in ("neutral", "neu", "neutral_sentiment", "2"):
            # Neutral: score maps around 0
            normalized = 0.0
            sentiment_label = SentimentLabel.NEUTRAL
        else:
            # Unknown label - try to parse as number
            try:
                label_num = float(label)
                if label_num > 0.5:
                    normalized = score
                    sentiment_label = SentimentLabel.POSITIVE
                elif label_num < 0.5:
                    normalized = -score
                    sentiment_label = SentimentLabel.NEGATIVE
                else:
                    normalized = 0.0
                    sentiment_label = SentimentLabel.NEUTRAL
            except ValueError:
                # Default to neutral
                normalized = 0.0
                sentiment_label = SentimentLabel.NEUTRAL

        return normalized, sentiment_label

    def analyze(self, text: str, language: Optional[str] = None) -> SentimentResult:
        """
        Analyze sentiment of a text.

        Args:
            text: Text to analyze
            language: Optional language code override

        Returns:
            SentimentResult with score, label, and confidence
        """
        self._ensure_models_loaded()

        # Detect language if not provided
        if language is None:
            language = self.detect_language(text)

        # Select appropriate model
        try:
            if language == "ar":
                model = get_arabic_sentiment_model()
            else:
                model = get_english_sentiment_model()
        except Exception as e:
            logger.warning(
                "Model selection failed, using English",
                language=language,
                error=str(e),
            )
            model = get_english_sentiment_model()
            language = "en"

        # Run inference
        try:
            result = model(text)[0]
            label = result["label"]
            confidence = result["score"]

            normalized_score, sentiment_label = self._normalize_score(label, confidence)

            return SentimentResult(
                text=text,
                score=normalized_score,
                label=sentiment_label,
                confidence=confidence,
                language=language,
            )
        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e), text=text[:100])
            # Return neutral sentiment on error
            return SentimentResult(
                text=text,
                score=0.0,
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                language=language,
            )

    def analyze_batch(
        self, texts: list[str], language: Optional[str] = None
    ) -> list[SentimentResult]:
        """
        Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze
            language: Optional language code override (applied to all texts)

        Returns:
            List of SentimentResult objects
        """
        self._ensure_models_loaded()

        results = []
        for text in texts:
            result = self.analyze(text, language)
            results.append(result)

        return results

    def get_text_hash(self, text: str) -> str:
        """
        Generate a hash for text caching.

        Args:
            text: Input text

        Returns:
            SHA256 hash of the text
        """
        return hashlib.sha256(text.encode()).hexdigest()


# Global instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get the sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


async def preload_models() -> None:
    """Preload sentiment models at startup."""
    logger.info("Preloading sentiment models...")
    analyzer = get_sentiment_analyzer()
    analyzer._ensure_models_loaded()
    logger.info("Sentiment models loaded")
