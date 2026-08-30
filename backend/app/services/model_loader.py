"""
Singleton model loader for NLP models.
Loads spaCy and sentence-transformer models once and caches them.
Model names are read from configuration to allow experimentation
with different models without code changes.
"""
import logging
from typing import Optional

import spacy
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_nlp = None
_st_model = None


def get_nlp():
    """Get the spaCy NLP pipeline (loaded once)."""
    global _nlp
    if _nlp is None:
        model_name = settings.SPACY_MODEL
        try:
            _nlp = spacy.load(model_name)
            logger.info(f"spaCy model loaded: {model_name}")
        except OSError:
            logger.error(
                f"spaCy model '{model_name}' not found. "
                f"Install it with: python -m spacy download {model_name}"
            )
            raise
    return _nlp


def get_sentence_model() -> SentenceTransformer:
    """Get the sentence-transformer model (loaded once)."""
    global _st_model
    if _st_model is None:
        model_name = settings.EMBEDDING_MODEL
        try:
            _st_model = SentenceTransformer(model_name)
            logger.info(f"Sentence-transformer model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model '{model_name}': {e}")
            raise
    return _st_model


def get_model_info() -> dict:
    """Return info about loaded models (useful for debugging/API responses)."""
    return {
        "spacy_model": settings.SPACY_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "spacy_loaded": _nlp is not None,
        "sentence_model_loaded": _st_model is not None,
    }

