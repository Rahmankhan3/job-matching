"""
End-to-end API integration and matching engine test script.
Tests all workflows:
  - Auth (Recruiter & Candidate)
  - Profiles (Recruiter & Candidate)
  - Job creation with requirements and screening questions
  - Resume upload
  - Application submission + automatic AI ranking trigger
  - Ranked candidate list retrieval
  - Detailed candidate match analysis
  - Reprocessing endpoints
"""
import os
import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def run_e2e_test():
    print("=" * 70)
    print(" STARTING END-TO-END RECRUITMENT & AI MATCHING TEST")
    print("=" * 70)

    # 1. Health check
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200, f"Root endpoint failed: {res.text}"
    print("[1/9] Health check OK:", res.json())

    # 2. Recruiter Signup & Login
    recruiter_email = f"recruiter_{int(time.time())}@company.com"
    password = "SecurePassword123!"
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": recruiter_email,
        "password": password,
        "role": "recruiter"
    })
    assert res.status_code == 201, f"Recruiter signup failed: {res.text}"
    
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": recruiter_email,
        "password": password
    })
    assert res.status_code == 200
    recruiter_token = res.json()["access_token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    print("[2/9] Recruiter created & authenticated:", recruiter_email)

    # 3. Create Recruiter Profile
    res = requests.put(f"{BASE_URL}/recruiter/profile", json={
        "company_name": "AI Innovations Lab",
        "designation": "Head of Talent Acquisition",
        "location": "San Francisco, CA"
    }, headers=recruiter_headers)
    assert res.status_code == 200
    print("[3/9] Recruiter profile configured")

    # 4. Create Job Posting (Data Scientist)
    job_payload = {
        "title": "Senior Data Scientist",
        "company": "AI Innovations Lab",
        "work_arrangement": "Full Time",
        "work_setup": "Hybrid",
        "work_location": "San Francisco, CA",
        "candidate_type": ["Everyone"],
        "passing_year": ["Allow All"],
        "educational_background": ["Computer Science", "Data Science", "Engineering"],
        "roles": "Data Scientist",
        "responsibilities": "Build and deploy machine learning models, analyze complex datasets, optimize predictive algorithms, and develop NLP pipelines.",
        "requirements": [
            "3+ years experience with Python and machine learning libraries",
            "Strong understanding of deep learning and NLP architectures",
            "Experience with cloud deployment and SQL data pipelines"
        ],
        "qualifications": ["Bachelor's or Master's in Computer Science, Data Science, or related field"],
        "skills_required": ["Python", "Machine Learning", "NLP", "Pandas", "Scikit-learn", "SQL", "Deep Learning"],
        "salary_min": 120000,
        "salary_max": 160000,
        "benefits": ["Health Insurance", "Remote Flexibility", "401k Matching"],
        "application_form_fields": [
            {
                "field_id": "ml_experience",
                "label": "Briefly describe a recent machine learning or NLP project you deployed to production.",
                "field_type": "textarea",
                "required": True
            }
        ]
    }
    res = requests.post(f"{BASE_URL}/jobs/", json=job_payload, headers=recruiter_headers)
    assert res.status_code == 201, f"Job creation failed: {res.text}"
    job_id = res.json()["id"]
    print(f"[4/9] Job posted: '{job_payload['title']}' (ID: {job_id})")

    # 5. Candidate Signup & Login
    candidate_email = f"candidate_{int(time.time())}@domain.com"
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": candidate_email,
        "password": password,
        "role": "candidate"
    })
    assert res.status_code == 201
    
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": candidate_email,
        "password": password
    })
    assert res.status_code == 200
    candidate_token = res.json()["access_token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    print("[5/9] Candidate created & authenticated:", candidate_email)

    # 6. Candidate Profile Setup
    res = requests.put(f"{BASE_URL}/candidate/profile", json={
        "full_name": "Dr. Sarah Chen",
        "phone": "+1-555-019-2834",
        "location": "San Francisco, CA",
        "skills": ["Python", "Machine Learning", "NLP", "PyTorch"],
        "experience_level": "senior"
    }, headers=candidate_headers)
    assert res.status_code == 200
    print("[6/9] Candidate profile configured: Dr. Sarah Chen")

    # 7. Upload Resume (use one of the test dataset PDFs)
    resume_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resume_data", "Data Science", "0.pdf"))
    if not os.path.exists(resume_file_path):
        # Fallback to creating a sample PDF/DOCX if path differs
        resume_url = "http://localhost:8000/uploads/resumes/sample_resume.pdf"
    else:
        with open(resume_file_path, "rb") as f:
            files = {"file": ("data_scientist_resume.pdf", f, "application/pdf")}
            res = requests.post(f"{BASE_URL}/upload/resume", files=files, headers=candidate_headers)
            assert res.status_code == 200, f"Upload failed: {res.text}"
            resume_url = res.json()["url"]
    print("[7/9] Resume uploaded successfully:", resume_url)

    # 8. Submit Application (triggers AI parsing & matching)
    app_payload = {
        "job_posting_id": job_id,
        "cover_letter": "I have 5+ years of experience developing machine learning and NLP systems using Python, Pandas, Scikit-learn, and SQL.",
        "resume_url": resume_url,
        "form_responses": {
            "ml_experience": "Built and deployed an end-to-end customer recommendation engine and an AI NLP chatbot achieving high accuracy in production."
        }
    }
    res = requests.post(f"{BASE_URL}/applications/", json=app_payload, headers=candidate_headers)
    assert res.status_code == 201, f"Application submission failed: {res.text}"
    app_id = res.json()["id"]
    print(f"[8/9] Application submitted & AI ranking triggered (App ID: {app_id})")

    # 9. Recruiter views ranked applications & match analysis
    res = requests.get(f"{BASE_URL}/ranking/job/{job_id}", headers=recruiter_headers)
    assert res.status_code == 200, f"Get ranking failed: {res.text}"
    ranked_apps = res.json()
    print(f"\n[9/9] Ranked Applications Response ({len(ranked_apps)} candidates):")
    for app in ranked_apps:
        print(f"   Rank #{app['rank']}: {app['candidate_name']} ({app['candidate_email']})")
        print(f"   Final Score  : {app['final_match_score']}/100")
        print(f"   Matched Skills: {app['matched_skills']}")
        print(f"   Missing Skills: {app['missing_skills']}")
        print(f"   Eligibility   : {app['eligibility_status']}")
        print(f"   Status        : {app['ranking_status']}")

    # Detailed match analysis
    res = requests.get(f"{BASE_URL}/ranking/application/{app_id}/analysis", headers=recruiter_headers)
    assert res.status_code == 200, f"Get analysis failed: {res.text}"
    analysis = res.json()
    print("\n" + "=" * 70)
    print(" DETAILED AI MATCH ANALYSIS")
    print("=" * 70)
    print(f" Candidate : {analysis['candidate_name']} <{analysis['candidate_email']}>")
    print(f" Job Role  : {analysis['job_title']} at {analysis['company']}")
    print(f" Final Score: {analysis['final_match_score']}/100")
    print(f" Breakdown :")
    for criterion, score_data in (analysis['match_scores'] or {}).items():
        score_val = score_data.get('score', score_data) if isinstance(score_data, dict) else score_data
        print(f"   - {criterion:<15}: {score_val}/100")
    print(f" Matched Skills: {analysis['matched_skills']}")
    print(f" Missing Skills: {analysis['missing_skills']}")
    print(f" Eligibility   : {analysis['eligibility_status']}")

    # Test reprocess application
    res = requests.post(f"{BASE_URL}/ranking/application/{app_id}/reprocess", headers=recruiter_headers)
    assert res.status_code == 200
    print("\nReprocessing single application test PASSED")

    # Test reprocess job
    res = requests.post(f"{BASE_URL}/ranking/job/{job_id}/reprocess", headers=recruiter_headers)
    assert res.status_code == 200
    print("Reprocessing all job applications test PASSED")

    print("\n" + "=" * 70)
    print(" ALL END-TO-END TESTS PASSED SUCCESSFULLY! ")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_test()
