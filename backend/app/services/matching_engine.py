"""
Hybrid candidate–job matching engine.

Computes a weighted relevance score across 6 criteria and returns a
detailed breakdown. This is an initial baseline implementation — the
weights are configurable starting points, not optimized parameters.

The feature extraction is structured so the scoring function can later
be replaced with a trained Learning-to-Rank model (e.g., XGBoost,
LightGBM) without rewriting feature computation.
"""
import logging
from typing import Optional, Dict, List

from app.config import settings
from app.services.skill_normalizer import normalize_skills
from app.services.embedding_service import (
    generate_resume_embeddings,
    generate_job_embeddings,
    compute_multi_similarity,
    compute_similarity,
)

logger = logging.getLogger(__name__)


def _get_weights() -> Dict[str, float]:
    """Read ranking weights from centralized configuration."""
    return {
        "skills": settings.RANKING_WEIGHT_SKILLS,
        "semantic": settings.RANKING_WEIGHT_SEMANTIC,
        "experience": settings.RANKING_WEIGHT_EXPERIENCE,
        "projects": settings.RANKING_WEIGHT_PROJECTS,
        "education": settings.RANKING_WEIGHT_EDUCATION,
        "screening": settings.RANKING_WEIGHT_SCREENING,
    }


# ── Criterion 1: Skills Match ────────────────────────────────────────────────

def _score_skills(jd_skills: list, resume_skills: list) -> dict:
    """Compute skill overlap using normalized canonical forms."""
    jd_normalized = set(normalize_skills(jd_skills))
    res_normalized = set(normalize_skills(resume_skills))

    jd_lower = {s.lower() for s in jd_normalized}
    res_lower_map = {s.lower(): s for s in res_normalized}

    if not jd_lower:
        return {"score": 100.0, "matched": sorted(res_normalized), "missing": []}

    matched = sorted(res_lower_map[s] for s in jd_lower & set(res_lower_map.keys()))
    missing = sorted(s for s in jd_normalized if s.lower() not in res_lower_map)
    score = (len(matched) / len(jd_lower)) * 100.0

    return {"score": round(score, 1), "matched": matched, "missing": missing}


# ── Criterion 2: Semantic Similarity ──────────────────────────────────────────

def _score_semantic(job_data: dict, parsed_resume: dict) -> dict:
    """Multi-faceted semantic similarity using pre-computed or on-demand embeddings."""
    resume_emb = generate_resume_embeddings(parsed_resume)
    job_emb = generate_job_embeddings(job_data)

    sim_scores = compute_multi_similarity(resume_emb, job_emb)

    # Weighted combination: overall gets most weight, section-level adds signal
    overall = sim_scores.get("overall", 0.0)
    exp_req = sim_scores.get("experience_requirements", 0.0)
    proj_resp = sim_scores.get("projects_responsibilities", 0.0)

    # 60% overall, 25% experience↔requirements, 15% projects↔responsibilities
    combined = overall * 0.60 + exp_req * 0.25 + proj_resp * 0.15
    score = combined * 100.0

    return {
        "score": round(score, 1),
        "overall_similarity": round(overall, 3),
        "experience_requirements_similarity": round(exp_req, 3),
        "projects_responsibilities_similarity": round(proj_resp, 3),
    }


# ── Criterion 3: Experience Relevance ─────────────────────────────────────────

def _score_experience(job_data: dict, parsed_resume: dict) -> dict:
    """
    Evaluate experience by quantity, technology overlap, role relevance,
    and total duration. Both duration and relevance matter — a short but
    relevant stint outweighs long irrelevant experience.
    """
    experiences = parsed_resume.get("experience") or []
    jd_skills = set(normalize_skills(job_data.get("skills_required") or []))
    jd_skills_lower = {s.lower() for s in jd_skills}
    jd_role = (job_data.get("roles") or "").strip()

    if not experiences:
        return {
            "score": 15.0, "summary": "No experience entries found",
            "entry_count": 0, "total_experience_months": 0,
        }

    entry_count = len(experiences)

    # Aggregate total duration from entries that have it
    total_months = sum(
        exp.get("duration_months") or 0 for exp in experiences
    )

    # Sub-score 1: experience entries + duration (up to 25 pts)
    # Having entries is good; having measurable duration is better
    entry_base = min(entry_count / 4, 1.0) * 15
    duration_base = min(total_months / 48, 1.0) * 10  # saturates at 4 years
    quantity_score = entry_base + duration_base

    # Sub-score 2: technology overlap across all experience (up to 40 pts)
    all_exp_tech = set()
    for exp in experiences:
        techs = normalize_skills(exp.get("technologies") or [])
        all_exp_tech.update(t.lower() for t in techs)

    tech_overlap = len(jd_skills_lower & all_exp_tech) / max(len(jd_skills_lower), 1)
    tech_score = tech_overlap * 40

    # Sub-score 3: role title relevance (up to 35 pts, semantic)
    role_titles = " ".join(exp.get("role", "") for exp in experiences)
    if jd_role and role_titles:
        role_sim = compute_similarity(jd_role, role_titles)
    else:
        role_sim = 0.3
    role_score = role_sim * 35

    total = quantity_score + tech_score + role_score

    summary_parts = [f"{entry_count} experience entr{'y' if entry_count == 1 else 'ies'}"]
    if total_months > 0:
        years = total_months // 12
        months = total_months % 12
        dur_str = f"{years}y {months}m" if years else f"{months}m"
        summary_parts.append(f"Duration: ~{dur_str}")
    overlap_skills = sorted(jd_skills_lower & all_exp_tech)
    if overlap_skills:
        summary_parts.append(f"Tech: {', '.join(overlap_skills[:5])}")

    return {
        "score": round(min(total, 100.0), 1),
        "summary": " · ".join(summary_parts),
        "entry_count": entry_count,
        "total_experience_months": total_months,
        "tech_overlap": overlap_skills,
    }


# ── Criterion 4: Project Relevance ───────────────────────────────────────────

def _score_projects(job_data: dict, parsed_resume: dict) -> dict:
    """
    Compare projects against JD using both technology overlap and semantic similarity.
    Projects are especially important for fresher/intern candidates.
    """
    projects = parsed_resume.get("projects") or []

    if not projects:
        return {"score": 10.0, "top_project": None, "project_count": 0}

    jd_skills = set(normalize_skills(job_data.get("skills_required") or []))
    jd_skills_lower = {s.lower() for s in jd_skills}
    jd_text = " ".join([
        job_data.get("roles") or "",
        job_data.get("responsibilities") or "",
        " ".join(job_data.get("skills_required") or []),
    ]).strip()

    if not jd_text:
        return {"score": 50.0, "top_project": projects[0].get("title"), "project_count": len(projects)}

    best_score = 0.0
    top_project = None

    for proj in projects:
        proj_text = f"{proj.get('title', '')} {proj.get('description', '')} {' '.join(proj.get('technologies', []))}"

        # Semantic similarity (weighted 60%)
        sem_sim = compute_similarity(jd_text, proj_text)

        # Technology overlap (weighted 40%)
        proj_techs = set(normalize_skills(proj.get("technologies") or []))
        proj_techs_lower = {t.lower() for t in proj_techs}
        if jd_skills_lower:
            tech_overlap = len(jd_skills_lower & proj_techs_lower) / len(jd_skills_lower)
        else:
            tech_overlap = 0.0

        combined = sem_sim * 0.6 + tech_overlap * 0.4
        if combined > best_score:
            best_score = combined
            top_project = proj

    # Quantity bonus: having more projects helps (up to 20 pts)
    quantity_bonus = min(len(projects) / 5, 1.0) * 20
    # Best project relevance (up to 80 pts)
    relevance_score = best_score * 80
    total = quantity_bonus + relevance_score

    return {
        "score": round(min(total, 100.0), 1),
        "top_project": top_project.get("title") if top_project else None,
        "top_project_data": top_project,
        "project_count": len(projects),
    }


# ── Criterion 5: Education / Eligibility Match ───────────────────────────────

def _score_education(job_data: dict, parsed_resume: dict) -> dict:
    """
    Check education against JD requirements and determine eligibility.
    Some conditions (e.g., passing year) are hard eligibility constraints,
    not just scoring features.
    """
    education = parsed_resume.get("education") or []
    score = 50.0
    eligibility_flags = []

    # Educational background match
    jd_edu = set(s.lower() for s in (job_data.get("educational_background") or []))
    if jd_edu and education:
        edu_matched = False
        for entry in education:
            degree = (entry.get("degree") or "").lower()
            field = (entry.get("field") or "").lower()
            for jd_e in jd_edu:
                if jd_e in degree or degree in jd_e or jd_e in field:
                    edu_matched = True
                    break
        if edu_matched:
            score += 25.0
        else:
            eligibility_flags.append("education_mismatch")

    # Passing year check — can be a hard constraint
    jd_years = job_data.get("passing_year") or []
    if jd_years and "Allow All" not in jd_years:
        year_matched = False
        for entry in education:
            yr = entry.get("graduation_year")
            if yr and str(yr) in jd_years:
                year_matched = True
                break
        if year_matched:
            score += 25.0
        else:
            eligibility_flags.append("passing_year_mismatch")
    else:
        score += 25.0  # no restriction = full marks

    # Candidate type check
    jd_candidate_types = [t.lower() for t in (job_data.get("candidate_type") or [])]
    if jd_candidate_types and "everyone" not in jd_candidate_types:
        # We can't definitively determine candidate type from resume alone,
        # so this is treated as informational rather than disqualifying
        pass

    return {
        "score": round(min(score, 100.0), 1),
        "entries": len(education),
        "eligibility_flags": eligibility_flags,
    }


def _determine_eligibility(education_result: dict) -> str:
    """Derive eligibility status from education scoring flags."""
    flags = education_result.get("eligibility_flags", [])
    if not flags:
        return "eligible"
    if "passing_year_mismatch" in flags:
        return "potentially_ineligible"
    return "partially_matching"


# ── Criterion 6: Screening Question Match ────────────────────────────────────

def _score_screening(job_data: dict, form_responses: dict) -> dict:
    """Score screening question answers using structured and semantic checks."""
    form_fields = job_data.get("application_form_fields") or []
    if not form_fields or not form_responses:
        return {"score": 70.0, "answered": 0, "total": len(form_fields)}

    answered = 0
    quality_scores = []

    for field in form_fields:
        fid = field.get("field_id")
        answer = form_responses.get(fid)

        if answer is None or (isinstance(answer, str) and not answer.strip()):
            if field.get("required"):
                quality_scores.append(0)
            continue

        answered += 1
        ftype = field.get("field_type", "text")

        if ftype in ("text", "textarea"):
            text = str(answer).strip()
            length = len(text)
            # Longer, more detailed answers score higher
            if length > 100:
                quality_scores.append(100)
            elif length > 30:
                quality_scores.append(70)
            elif length > 0:
                quality_scores.append(40)
        elif ftype == "checkbox":
            quality_scores.append(80)
        else:
            quality_scores.append(70)

    avg = sum(quality_scores) / len(quality_scores) if quality_scores else 50.0

    return {"score": round(avg, 1), "answered": answered, "total": len(form_fields)}


# ── Feature Extraction ────────────────────────────────────────────────────────

def extract_match_features(
    job_data: dict,
    parsed_resume: dict,
    form_responses: Optional[dict] = None,
) -> dict:
    """
    Extract all matching features as a flat dict.
    This is the interface point for a future Learning-to-Rank model —
    the features dict can be fed directly to XGBoost/LightGBM.
    """
    jd_skills = job_data.get("skills_required") or []
    resume_skills = parsed_resume.get("skills") or []

    skills_result = _score_skills(jd_skills, resume_skills)
    semantic_result = _score_semantic(job_data, parsed_resume)
    experience_result = _score_experience(job_data, parsed_resume)
    project_result = _score_projects(job_data, parsed_resume)
    education_result = _score_education(job_data, parsed_resume)
    screening_result = _score_screening(job_data, form_responses or {})

    return {
        "skills": skills_result,
        "semantic": semantic_result,
        "experience": experience_result,
        "projects": project_result,
        "education": education_result,
        "screening": screening_result,
    }


# ── Main Scoring ──────────────────────────────────────────────────────────────

def compute_match_score(
    job_data: dict,
    parsed_resume: dict,
    form_responses: Optional[dict] = None,
    cover_letter: Optional[str] = None,
) -> dict:
    """
    Compute the hybrid baseline match score for a candidate against a job.

    Returns a structured result containing the weighted final score,
    per-criterion scores, matched/missing skills, eligibility status,
    and metadata for recruiter display.
    """
    # Combine cover letter with summary for richer semantic signal
    if cover_letter:
        existing_summary = parsed_resume.get("summary") or ""
        combined = f"{existing_summary} {cover_letter}".strip()
        parsed_resume = {**parsed_resume, "summary": combined}

    features = extract_match_features(job_data, parsed_resume, form_responses)
    weights = _get_weights()

    # Weighted baseline score
    final = (
        features["skills"]["score"]     * weights["skills"]
        + features["semantic"]["score"] * weights["semantic"]
        + features["experience"]["score"] * weights["experience"]
        + features["projects"]["score"]  * weights["projects"]
        + features["education"]["score"] * weights["education"]
        + features["screening"]["score"] * weights["screening"]
    )

    eligibility = _determine_eligibility(features["education"])

    # Build metadata for recruiter display
    exp_entries = parsed_resume.get("experience") or []
    experience_summary = features["experience"].get("summary", "")
    if exp_entries:
        first_role = exp_entries[0].get("role", "")
        if first_role:
            experience_summary = f"{first_role} · {experience_summary}"

    return {
        "final_score": round(final, 1),
        "scores": features,
        "matched_skills": features["skills"]["matched"],
        "missing_skills": features["skills"]["missing"],
        "eligibility_status": eligibility,
        "ranking_metadata": {
            "experience_summary": experience_summary,
            "top_project": features["projects"].get("top_project"),
            "top_project_data": features["projects"].get("top_project_data"),
            "project_count": features["projects"].get("project_count", 0),
            "experience_count": features["experience"].get("entry_count", 0),
            "education_count": features["education"].get("entries", 0),
            "screening_answered": features["screening"].get("answered", 0),
            "screening_total": features["screening"].get("total", 0),
            "weights_used": weights,
        },
    }
