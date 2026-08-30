"""
Batch processor for Kaggle Resume Dataset experiments.

This module is designed to run offline/experimental processing over
large directories of resume PDFs. It uses the exact same parsing and
normalization pipeline as production but does not touch MongoDB or the
web application state.

Outputs structured JSON files and a comprehensive evaluation report.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.resume_parser import parse_resume

logger = logging.getLogger(__name__)


def process_single_resume(file_path: str, category: str = None) -> Dict[str, Any]:
    """Parse a single resume and return the result along with metadata."""
    try:
        start_time = datetime.now()
        parsed = parse_resume(file_path)
        duration = (datetime.now() - start_time).total_seconds()
        
        if not parsed:
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "category": category,
                "status": "failed",
                "error": "Parser returned None (insufficient text or unreadable PDF)",
                "duration_seconds": round(duration, 3),
            }
            
        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "category": category,
            "status": "success",
            "duration_seconds": round(duration, 3),
            "parsed_data": parsed.model_dump(mode="json")
        }
    except Exception as e:
        logger.error(f"Batch processing failed for {file_path}: {e}")
        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "category": category,
            "status": "error",
            "error": str(e),
            "duration_seconds": 0,
        }


def generate_batch_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive summary statistics for a batch processing run."""
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    failed = total - success
    
    total_duration = sum(r.get("duration_seconds", 0) for r in results)
    avg_duration = (total_duration / total) if total > 0 else 0
    
    categories: Dict[str, Dict[str, int]] = {}
    skill_counts: Dict[str, int] = {}
    failure_reasons: Dict[str, int] = {}
    
    # Section extraction statistics
    section_stats = {
        "has_name": 0,
        "has_email": 0,
        "has_phone": 0,
        "has_location": 0,
        "has_linkedin": 0,
        "has_github": 0,
        "has_skills": 0,
        "has_experience": 0,
        "has_projects": 0,
        "has_education": 0,
        "has_certifications": 0,
        "has_summary": 0,
    }
    
    total_skills_extracted = 0
    total_exp_entries = 0
    total_proj_entries = 0
    total_edu_entries = 0

    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0, "failed": 0}
        categories[cat]["total"] += 1
        
        if r["status"] == "success":
            categories[cat]["success"] += 1
            data = r.get("parsed_data", {})
            pinfo = data.get("personal_info", {}) or {}
            
            if pinfo.get("name"):
                section_stats["has_name"] += 1
            if pinfo.get("email"):
                section_stats["has_email"] += 1
            if pinfo.get("phone"):
                section_stats["has_phone"] += 1
            if pinfo.get("location"):
                section_stats["has_location"] += 1
            if pinfo.get("linkedin"):
                section_stats["has_linkedin"] += 1
            if pinfo.get("github"):
                section_stats["has_github"] += 1
                
            skills = data.get("skills", []) or []
            if skills:
                section_stats["has_skills"] += 1
                total_skills_extracted += len(skills)
                for skill in skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                    
            exp = data.get("experience", []) or []
            if exp:
                section_stats["has_experience"] += 1
                total_exp_entries += len(exp)
                
            proj = data.get("projects", []) or []
            if proj:
                section_stats["has_projects"] += 1
                total_proj_entries += len(proj)
                
            edu = data.get("education", []) or []
            if edu:
                section_stats["has_education"] += 1
                total_edu_entries += len(edu)
                
            certs = data.get("certifications", []) or []
            if certs:
                section_stats["has_certifications"] += 1
                
            if data.get("summary"):
                section_stats["has_summary"] += 1
        else:
            categories[cat]["failed"] += 1
            err = r.get("error", "Unknown error")
            failure_reasons[err] = failure_reasons.get(err, 0) + 1

    # Calculate section detection percentages
    section_rates = {}
    if success > 0:
        for sec, count in section_stats.items():
            section_rates[sec] = {
                "count": count,
                "percentage": f"{(count / success * 100):.1f}%"
            }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_processed": total,
        "success_count": success,
        "failed_count": failed,
        "success_rate": f"{(success / total * 100):.1f}%" if total > 0 else "0%",
        "total_duration_seconds": round(total_duration, 2),
        "avg_duration_seconds": round(avg_duration, 3),
        "section_extraction_rates": section_rates,
        "averages_per_successful_resume": {
            "avg_skills_per_resume": round(total_skills_extracted / success, 1) if success > 0 else 0,
            "avg_experience_entries": round(total_exp_entries / success, 1) if success > 0 else 0,
            "avg_project_entries": round(total_proj_entries / success, 1) if success > 0 else 0,
            "avg_education_entries": round(total_edu_entries / success, 1) if success > 0 else 0,
        },
        "top_15_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15],
        "categories_breakdown": categories,
        "failure_reasons": failure_reasons,
    }


def process_dataset(
    dataset_dir: str,
    output_dir: Optional[str] = None,
    limit: Optional[int] = None,
    categories_filter: Optional[List[str]] = None,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process a directory structure where subdirectories are categories.
    Optionally persists structured outputs and the batch report to disk.
    
    Args:
        dataset_dir: Root directory containing category folders with resume PDFs.
        output_dir: Optional directory to store individual parsed JSONs and batch report.
        limit: Max resumes to process across categories.
        categories_filter: Optional list of category names to include (case-insensitive).
    """
    if not dataset_dir or not os.path.isdir(dataset_dir):
        logger.error(f"Dataset directory not found: {dataset_dir}")
        return [], {"error": f"Directory not found: {dataset_dir}"}
        
    results = []
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    target_categories = [c.lower() for c in categories_filter] if categories_filter else None

    # Walk directory
    for root, dirs, files in os.walk(dataset_dir):
        category = os.path.basename(root)
        
        # Skip root directory if it has no direct PDFs and we want to process subdirs
        if target_categories and category.lower() not in target_categories:
            continue
            
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        for file in pdf_files:
            if limit and len(results) >= limit:
                break
                
            file_path = os.path.join(root, file)
            result = process_single_resume(file_path, category)
            results.append(result)
            
            # Save single resume parsed JSON if output directory is provided
            if output_dir and result["status"] == "success":
                cat_slug = category.replace(" ", "_").lower()
                cat_out_dir = os.path.join(output_dir, cat_slug)
                os.makedirs(cat_out_dir, exist_ok=True)
                
                base_name = os.path.splitext(file)[0]
                out_path = os.path.join(cat_out_dir, f"{base_name}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result["parsed_data"], f, indent=2, ensure_ascii=False)
            
            if len(results) % 25 == 0:
                logger.info(f"Processed {len(results)} resumes...")
                
        if limit and len(results) >= limit:
            break
            
    report = generate_batch_report(results)
    
    # Save batch report to output directory
    if output_dir:
        report_path = os.path.join(output_dir, "batch_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved batch report to {report_path}")
        
    return results, report
