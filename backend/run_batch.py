#!/usr/bin/env python3
"""
CLI tool for batch processing resume datasets and generating extraction statistics.

Usage examples:
    # Process 20 resumes from the default resume_data folder and save to data/processed
    python run_batch.py --limit 20

    # Process specific categories with custom output directory
    python run_batch.py --categories "Data Science,Python Developer" --output-dir data/processed --limit 50

    # Process full dataset
    python run_batch.py --dataset-dir ../resume_data --output-dir data/processed
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# Add backend directory to sys.path so app imports work seamlessly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.config import settings
from app.services.batch_processor import process_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_batch")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch Resume Parsing & Evaluation CLI Tool"
    )
    
    # Default candidate dataset paths (checks ../resume_data, ./resume_data, or config)
    default_dataset = settings.DATASET_DIR or os.path.join(CURRENT_DIR, "..", "resume_data")
    if not os.path.isdir(default_dataset):
        default_dataset = os.path.join(CURRENT_DIR, "resume_data")
        
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=default_dataset,
        help=f"Path to resume dataset folder (default: {default_dataset})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(CURRENT_DIR, "data", "processed"),
        help="Path to save processed JSON files and batch report (default: backend/data/processed)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit total number of resumes to process (e.g., 20 for quick test)",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated category names to filter (e.g., 'Data Science,Python Developer')",
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    dataset_dir = os.path.abspath(args.dataset_dir)
    output_dir = os.path.abspath(args.output_dir)
    categories_filter = (
        [c.strip() for c in args.categories.split(",") if c.strip()]
        if args.categories
        else None
    )
    
    print("=" * 70)
    print(" AI Resume Parsing & Batch Dataset Processor")
    print("=" * 70)
    print(f" Dataset Directory : {dataset_dir}")
    print(f" Output Directory  : {output_dir}")
    print(f" Categories Filter : {categories_filter or 'ALL'}")
    print(f" Limit             : {args.limit or 'ALL'}")
    print("=" * 70)
    
    if not os.path.isdir(dataset_dir):
        print(f"\n[ERROR] Dataset directory not found: {dataset_dir}")
        print("\nPlease ensure the dataset directory exists or specify via --dataset-dir.")
        print("Expected structure:")
        print("  resume_data/")
        print("    ├── Data Science/")
        print("    │     ├── resume1.pdf")
        print("    │     └── resume2.pdf")
        print("    └── Python Developer/")
        print("          └── resume3.pdf\n")
        sys.exit(1)
        
    start_time = datetime.now()
    results, report = process_dataset(
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        limit=args.limit,
        categories_filter=categories_filter,
    )
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print(" Batch Processing Summary")
    print("=" * 70)
    print(f" Total Processed    : {report.get('total_processed', 0)}")
    print(f" Successful         : {report.get('success_count', 0)} ({report.get('success_rate', '0%')})")
    print(f" Failed             : {report.get('failed_count', 0)}")
    print(f" Total Duration     : {round(total_time, 2)}s")
    print(f" Avg Time / Resume  : {report.get('avg_duration_seconds', 0)}s")
    
    print("\n Section Extraction Rates (on successful parses):")
    for sec, stats in report.get("section_extraction_rates", {}).items():
        print(f"   - {sec:<22}: {stats['count']:>4} ({stats['percentage']})")
        
    print("\n Averages per Resume:")
    for k, v in report.get("averages_per_successful_resume", {}).items():
        print(f"   - {k:<25}: {v}")
        
    print("\n Top Extracted Skills:")
    for skill, count in report.get("top_15_skills", []):
        print(f"   - {skill:<20}: {count}")
        
    print("\n Category Breakdown:")
    for cat, stat in report.get("categories_breakdown", {}).items():
        print(f"   - {cat:<25}: Total {stat['total']}, Success {stat['success']}, Failed {stat['failed']}")
        
    if report.get("failure_reasons"):
        print("\n Failure Reasons:")
        for reason, count in report.get("failure_reasons", {}).items():
            print(f"   - {reason}: {count}")
            
    print("=" * 70)
    print(f" Results & Report saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
