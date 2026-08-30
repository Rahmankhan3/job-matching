"""
Embedding generation and semantic similarity service.

Generates vector representations for resume sections and job descriptions
using sentence-transformers. Designed so the underlying model can be swapped
via configuration (e.g., different sentence-transformer variants, or future
TF-IDF/BM25 baselines) without changing calling code.
"""
import logging
from typing import List, Optional, Dict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.services.model_loader import get_sentence_model

logger = logging.getLogger(__name__)

# Maximum text length sent to the model (truncated to stay within token limits)
_MAX_TEXT_LEN = 2000


def _safe_encode(texts: List[str]) -> Optional[np.ndarray]:
    """Encode texts into embeddings, returning None on failure."""
    try:
        model = get_sentence_model()
        # Truncate long texts to avoid token limit issues
        truncated = [t[:_MAX_TEXT_LEN] for t in texts]
        return model.encode(truncated, show_progress_bar=False)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts."""
    if not text_a or not text_b:
        return 0.0
    embeddings = _safe_encode([text_a, text_b])
    if embeddings is None:
        return 0.0
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0.0, min(1.0, sim)))


def generate_resume_embeddings(parsed_resume: dict) -> Dict[str, Optional[List[float]]]:
    """
    Generate semantic embeddings for meaningful resume sections.

    Returns a dict with embedding vectors (as float lists for MongoDB storage):
      - overall: combined resume text
      - experience: combined experience descriptions
      - projects: combined project descriptions
    """
    # Build section texts
    experience_parts = []
    for exp in parsed_resume.get("experience") or []:
        role = exp.get("role", "")
        desc = exp.get("description", "")
        experience_parts.append(f"{role} {desc}".strip())

    project_parts = []
    for proj in parsed_resume.get("projects") or []:
        title = proj.get("title", "")
        desc = proj.get("description", "")
        techs = " ".join(proj.get("technologies") or [])
        project_parts.append(f"{title} {desc} {techs}".strip())

    overall_parts = []
    if parsed_resume.get("summary"):
        overall_parts.append(parsed_resume["summary"])
    overall_parts.extend(experience_parts)
    overall_parts.extend(project_parts)
    skills_text = " ".join(parsed_resume.get("skills") or [])
    if skills_text:
        overall_parts.append(skills_text)
    if not overall_parts:
        overall_parts.append(parsed_resume.get("raw_text", "")[:3000])

    overall_text = " ".join(overall_parts).strip()
    experience_text = " ".join(experience_parts).strip()
    project_text = " ".join(project_parts).strip()

    # Batch encode all non-empty sections
    texts_to_encode = []
    labels = []
    for label, text in [("overall", overall_text), ("experience", experience_text), ("projects", project_text)]:
        if text:
            texts_to_encode.append(text)
            labels.append(label)

    result = {"overall": None, "experience": None, "projects": None}

    if not texts_to_encode:
        return result

    embeddings = _safe_encode(texts_to_encode)
    if embeddings is None:
        return result

    for i, label in enumerate(labels):
        result[label] = embeddings[i].tolist()

    return result


def generate_job_embeddings(job_data: dict) -> Dict[str, Optional[List[float]]]:
    """
    Generate semantic embeddings for job description sections.

    Returns:
      - overall: combined job text
      - responsibilities: responsibilities text
      - requirements: requirements text
    """
    roles = job_data.get("roles") or ""
    responsibilities = job_data.get("responsibilities") or ""
    requirements = " ".join(job_data.get("requirements") or [])
    qualifications = " ".join(job_data.get("qualifications") or [])
    skills = " ".join(job_data.get("skills_required") or [])

    overall_text = " ".join(p for p in [roles, responsibilities, requirements, qualifications, skills] if p).strip()
    resp_text = responsibilities.strip()
    req_text = f"{requirements} {qualifications}".strip()

    texts_to_encode = []
    labels = []
    for label, text in [("overall", overall_text), ("responsibilities", resp_text), ("requirements", req_text)]:
        if text:
            texts_to_encode.append(text)
            labels.append(label)

    result = {"overall": None, "responsibilities": None, "requirements": None}

    if not texts_to_encode:
        return result

    embeddings = _safe_encode(texts_to_encode)
    if embeddings is None:
        return result

    for i, label in enumerate(labels):
        result[label] = embeddings[i].tolist()

    return result


def compute_multi_similarity(
    resume_embeddings: Dict[str, Optional[List[float]]],
    job_embeddings: Dict[str, Optional[List[float]]],
) -> Dict[str, float]:
    """
    Compute multiple semantic similarity scores between resume and job embeddings.

    Returns scores for:
      - overall: resume_overall ↔ job_overall
      - experience_requirements: resume_experience ↔ job_requirements
      - projects_responsibilities: resume_projects ↔ job_responsibilities
    """
    scores = {
        "overall": 0.0,
        "experience_requirements": 0.0,
        "projects_responsibilities": 0.0,
    }

    pairs = [
        ("overall", "overall", "overall"),
        ("experience", "requirements", "experience_requirements"),
        ("projects", "responsibilities", "projects_responsibilities"),
    ]

    for resume_key, job_key, score_key in pairs:
        r_emb = resume_embeddings.get(resume_key)
        j_emb = job_embeddings.get(job_key)
        if r_emb is not None and j_emb is not None:
            sim = cosine_similarity([r_emb], [j_emb])[0][0]
            scores[score_key] = float(max(0.0, min(1.0, sim)))

    return scores
