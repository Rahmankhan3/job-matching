# Comprehensive Architecture & System Guide
## Project: AI and NLP-Based Platform for Talent Discovery and Acquisition

---

## 1. Executive Summary & Design Philosophy

The platform is designed around a **modular, layered architecture** using **FastAPI**, **MongoDB (PyMongo Async)**, and an **AI/NLP pipeline** combining **spaCy**, **Sentence-Transformers (`all-MiniLM-L6-v2`)**, **RapidOCR/pypdfium2**, and a **6-factor matching engine**.

### Core Design Principles
1. **Layered Separation of Concerns**: Routes handle HTTP protocols and validation; Services handle business logic and AI/NLP computation; Models define strict data schemas; Database manages async persistence and indexing.
2. **Asynchronous Non-Blocking Execution**: Database operations utilize asynchronous non-blocking I/O via Python `asyncio` and `pymongo.AsyncMongoClient`.
3. **Parse Once, Reuse Everywhere**: Candidate resumes are parsed into canonical, structured representations on upload/first application and stored in the `parsed_resumes` collection. Subsequent applications reuse this data without re-parsing.
4. **Research-Extensible Architecture**: The feature extraction layer (extracting skill scores, semantic vectors, experience metrics, project relevance, education flags, and screening quality) is **completely decoupled** from the final ranking algorithm. The current baseline (`hybrid-baseline-v1`) can be replaced with classical baselines (TF-IDF, BM25) or Machine Learning / Learning-to-Rank models (XGBoost, LightGBM Ranker) without modifying the parsing or application workflows.

---

## 2. Directory Structure & File Map

```text
backend/
├── app/
│   ├── config.py                  # Centralized configuration (weights, models, env variables)
│   ├── database.py                # Async MongoDB connection, collection references, and indexes
│   ├── main.py                    # FastAPI application initialization, lifespan, CORS, and routing
│   │
│   ├── middleware/
│   │   └── auth_middleware.py     # JWT token decoding and role-based guards (Candidate vs Recruiter)
│   │
│   ├── models/                    # Pydantic data contracts (Data Validation & Serialization)
│   │   ├── user.py                # User account, signup, login, and DB representation
│   │   ├── candidate_profile.py   # Candidate profile models
│   │   ├── recruiter_profile.py   # Recruiter profile and company review models
│   │   ├── job.py                 # Job posting, visibility, screening questions, and update models
│   │   ├── application.py         # Application submission and status tracking models
│   │   ├── application_view.py    # DTO views for Candidate and Recruiter application dashboards
│   │   ├── parsed_resume.py       # Strongly-typed schema for structured parsed resumes
│   │   └── ranking.py             # Ranking summaries, score breakdowns, and analysis response schemas
│   │
│   ├── routes/                    # REST API Controllers (HTTP endpoints)
│   │   ├── auth.py                # POST /auth/signup, POST /auth/login
│   │   ├── candidate.py           # GET /candidate/profile, PUT /candidate/profile
│   │   ├── recruiter.py           # GET /recruiter/profile, PUT /recruiter/profile
│   │   ├── jobs.py                # GET /jobs, POST /jobs, GET /jobs/{id}, PATCH /jobs/{id}, DELETE /jobs/{id}
│   │   ├── applications.py        # POST /applications, GET /my-applications, GET /job/{id}, PUT /{id}/status
│   │   ├── upload.py              # POST /upload/resume, POST /upload/logo
│   │   └── ranking.py             # GET /ranking/job/{id}, GET /analysis, POST /reprocess
│   │
│   ├── services/                  # Business Logic & Core NLP Services
│   │   ├── user_service.py        # Password hashing, user creation, and authentication
│   │   ├── profile_service.py     # Upsert logic for candidate and recruiter profiles
│   │   ├── job_service.py         # Job creation, querying, updates, and deactivation
│   │   ├── application_service.py # Application validation, duplicate checks, and submission
│   │   ├── model_loader.py        # Singleton model manager (spaCy & SentenceTransformers)
│   │   ├── skill_normalizer.py    # 120+ canonical skill taxonomy mapping & free-text extraction
│   │   ├── resume_parser.py       # PDF/DOCX/OCR text extraction, section splitting, NER, and parsing
│   │   ├── embedding_service.py   # Multi-section vector embedding generation and cosine similarity
│   │   ├── matching_engine.py     # 6-criterion feature extraction and hybrid weighted scoring
│   │   ├── ranking_service.py     # End-to-end ranking orchestration, caching, and reprocessing
│   │   └── batch_processor.py     # Offline dataset batch processing and extraction statistics
│   │
│   └── utils/
│       ├── jwt.py                 # JWT access token creation and decoding
│       └── password.py            # Argon2 password hashing and verification
│
├── data/
│   └── processed/                 # Offline experiment output JSONs & batch_report.json
├── run_batch.py                   # Standalone CLI tool to evaluate resume datasets
├── test_api_e2e.py                # Automated end-to-end integration test suite
├── requirements.txt               # Project dependencies
└── .env                           # Environment variables
```

---

## 3. Architecture Layer-by-Layer

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  (Frontend React / Vite, Swagger UI /docs, CLI run_batch)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Router Layer                     │
│   /auth    /candidate    /recruiter    /jobs    /ranking    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Depends() Guards
┌──────────────────────────────▼──────────────────────────────┐
│               Middleware & Authentication                   │
│   JWT Bearer Verification  •  Argon2  •  Role Authorization │
└──────────────────────────────┬──────────────────────────────┘
                               │ Strongly-typed DTOs
┌──────────────────────────────▼──────────────────────────────┐
│                   Service & Business Logic                  │
│  application_service • job_service • profile_service        │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
┌─────────────────────────────┐       ┌──────────────────────────────┐
│     AI / NLP Subsystem      │       │     Database & Storage       │
│ • resume_parser (OCR/NER)   │       │ • MongoDB Async Client       │
│ • skill_normalizer          │       │ • users, jobs, applications  │
│ • model_loader (Singleton)  │       │ • candidate_profiles         │
│ • embedding_service         │       │ • recruiter_profiles         │
│ • matching_engine (6-factor)│       │ • parsed_resumes (Reusable)  │
│ • ranking_service           │       │ • Static /uploads directory  │
└─────────────────────────────┘       └──────────────────────────────┘
```

---

### Layer 1: Configuration & Database (`config.py`, `database.py`)

* **`app/config.py`**:
  * Uses `pydantic-settings` (`BaseSettings`) to read and validate environment variables from `.env`.
  * Centralizes database credentials, JWT parameters, AI model selections (`all-MiniLM-L6-v2`, `en_core_web_sm`), model versions (`hybrid-baseline-v1`), and **baseline ranking weights**:
    * Skills: 25%, Semantic: 20%, Experience: 25%, Projects: 15%, Education: 5%, Screening: 10%.
* **`app/database.py`**:
  * Initializes the asynchronous MongoDB client (`AsyncMongoClient`).
  * Defines global collection handles (`users`, `jobs`, `applications`, `candidate_profiles`, `recruiter_profiles`, `parsed_resumes`).
  * `create_indexes()` executes during startup to enforce performance and uniqueness constraints:
    * `users`: `email` (unique)
    * `applications`: `(candidate_id, job_posting_id)` (unique compound index — prevents duplicate applications)
    * `applications`: `(job_posting_id, final_match_score: -1)` (compound index for fast sorted retrieval by rank)
    * `parsed_resumes`: `candidate_id` (unique — enforces single canonical parsed record per candidate)

---

### Layer 2: Authentication & Security (`auth_middleware.py`, `jwt.py`, `password.py`)

* **Password Security**: Uses **Argon2** (via `passlib.context.CryptContext` with 64 MB memory cost, 3 iterations, 2-thread parallelism) to resist GPU brute-force attacks.
* **Token Lifecycle**: JWT tokens signed using HS256 containing `user_id`, `email`, and `role`. Default expiry: 30 minutes.
* **Role-Based Access Control (RBAC)**:
  * `get_current_user`: Decodes Bearer token from header, looks up the user in MongoDB, raises HTTP 401 if expired/invalid.
  * `get_current_candidate`: Verifies `role == "candidate"` (raises HTTP 403 otherwise).
  * `get_current_recruiter`: Verifies `role == "recruiter"` (raises HTTP 403 otherwise).
  * `get_optional_user`: Allows unauthenticated public access while attaching user context if a token is present (e.g., viewing public job listings while highlighting whether the user already applied).

---

### Layer 3: Data Contracts & Models (`app/models/`)

Every request and response adheres to explicit Pydantic schemas:
1. **`user.py`**: `UserCreate`, `LoginRequest`, `User`, `UserInDB`.
2. **`job.py`**: `JobPostingCreate`, `JobPostingUpdate`, `JobPosting` with fields for salary, requirements, eligibility criteria, and custom screening questions (`ApplicationFormField`).
3. **`candidate_profile.py`** & **`recruiter_profile.py`**: Profile management schemas with `upsert` support.
4. **`parsed_resume.py`**:
   ```python
   class ParsedResume(BaseModel):
       personal_info: PersonalInfo       # name, email, phone, location, linkedin, github
       skills: List[str]                 # normalized canonical skill list
       skill_evidence: List[SkillEvidence] # provenance tracking where skills appeared
       experience: List[ExperienceEntry] # role, company, duration, duration_months, tech
       projects: List[ProjectEntry]     # title, description, technologies
       education: List[EducationEntry]   # degree, field, institution, graduation_year
       certifications: List[CertificationEntry]
       summary: Optional[str]
       raw_text: str
       parser_version: str
       parsed_at: Optional[datetime]
   ```
5. **`ranking.py`**: `MatchScores` (6 criteria), `CandidateRankingSummary` (ranked list view), and `RankingAnalysisResponse` (detailed explainability view).

---

### Layer 4: AI/NLP Subsystem & Matching Engine

#### 1. Model Singleton Manager (`model_loader.py`)
NLP models are heavy (hundreds of megabytes). Initializing `SentenceTransformer` inside API endpoints causes severe memory bloat and latency. `model_loader.py` implements a **thread-safe singleton cache** (`get_nlp()` and `get_sentence_model()`), ensuring models load once at boot time and remain in memory for instant inference.

#### 2. Robust Resume Parser & OCR Fallback (`resume_parser.py`)
* **Text Extraction**:
  * For standard PDFs $\rightarrow$ `pdfplumber` extracts text streams.
  * **OCR Fallback**: If extracted text has fewer than 30 characters (image-rendered PDF), `pypdfium2` renders pages at $2\times$ scale to numpy arrays and executes `RapidOCR` to extract text lines.
  * For DOCX $\rightarrow$ `python-docx` iterates through paragraphs.
* **Section Segmentation**: Regular expressions with case-insensitive boundary detection identify 6 core sections (`experience`, `education`, `projects`, `skills`, `certifications`, `summary`), accommodating layout variations (e.g. "Work History" vs "Employment History").
* **NER & Regex Information Extraction**:
  * Names and locations extracted using spaCy entity recognition (`PERSON`, `GPE`).
  * Emails, phone numbers, GitHub, and LinkedIn extracted via pre-compiled regex.
  * Date intervals (e.g. `"05/2018 - Aug 2021"`) are parsed into normalized `duration_months`.

#### 3. Canonical Skill Normalizer (`skill_normalizer.py`)
Maintains a centralized lookup map (`CANONICAL_SKILLS`) with 120+ technologies:
* Handles aliases and typos (e.g. `ReactJS`, `react.js`, `React JS` $\rightarrow$ `React`; `k8s` $\rightarrow$ `Kubernetes`; `sklearn` $\rightarrow$ `Scikit-learn`).
* Uses word-boundary regex patterns sorted by string length descending so composite names match before single words (e.g. `"machine learning"` matches before `"machine"`).
* Attaches **provenance evidence**: records whether a skill was identified in the `skills_section`, `experience:0`, or `project:1`.

#### 4. Multi-Section Embedding Service (`embedding_service.py`)
Rather than compressing an entire resume into a single vector (which washes out specific qualifications), representations are generated at multiple granularities:
* **Resume Vectors**:
  1. `overall`: Summary + Experience + Projects + Skills
  2. `experience`: Consolidated job roles and descriptions
  3. `projects`: Consolidated project descriptions and tech stacks
* **Job Vectors**:
  1. `overall`: Roles + Responsibilities + Requirements + Qualifications + Skills
  2. `responsibilities`: Primary duties
  3. `requirements`: Mandatory qualifications & skills
* Computes multi-angle cosine similarities:
  $$\text{sim}_{\text{overall}} = \cos(\mathbf{e}_{\text{res\_all}}, \mathbf{e}_{\text{jd\_all}})$$
  $$\text{sim}_{\text{exp\_req}} = \cos(\mathbf{e}_{\text{res\_exp}}, \mathbf{e}_{\text{jd\_req}})$$
  $$\text{sim}_{\text{proj\_resp}} = \cos(\mathbf{e}_{\text{res\_proj}}, \mathbf{e}_{\text{jd\_resp}})$$

#### 5. 6-Factor Matching Engine (`matching_engine.py`)
Computes 6 independent scores (each scaled $0 - 100$):
1. **Skill Match ($S_{\text{skills}}$)**: Normalized intersection of candidate skills vs job required skills. Returns `matched_skills` and `missing_skills`.
2. **Semantic Similarity ($S_{\text{semantic}}$)**: Combined section-level cosine similarity ($0.60 \cdot \text{overall} + 0.25 \cdot \text{exp} + 0.15 \cdot \text{proj}$).
3. **Experience Relevance ($S_{\text{exp}}$)**: Evaluates role semantic alignment ($35\%$), technology overlap in experience ($40\%$), and quantity + duration in months ($25\%$).
4. **Project Relevance ($S_{\text{proj}}$)**: Evaluates the candidate's strongest matching project via semantic similarity ($60\%$) and technology overlap ($40\%$), plus project count bonus.
5. **Education & Eligibility ($S_{\text{edu}}$)**: Evaluates degree level, field of study, and graduation year restrictions. Flags candidates as `eligible`, `partially_matching`, or `potentially_ineligible`.
6. **Screening Response ($S_{\text{screen}}$)**: Analyzes candidate responses to recruiter-defined screening questions.

**Weighted Final Score**:
$$\text{Final Score} = \sum_{i=1}^{6} (S_i \times w_i)$$

---

## 4. API Endpoints Reference

### Authentication (`/auth`)
* `POST /auth/signup`: Create a candidate or recruiter account.
* `POST /auth/login`: Authenticate email + password, returns JWT token and user info.

### Candidate Profile (`/candidate`)
* `GET /candidate/profile`: Retrieve candidate profile.
* `PUT /candidate/profile`: Upsert candidate profile (name, phone, location, skills, experience level).

### Recruiter Profile (`/recruiter`)
* `GET /recruiter/profile`: Retrieve recruiter company profile.
* `PUT /recruiter/profile`: Upsert recruiter company profile.

### Jobs (`/jobs`)
* `GET /jobs/`: Browse active jobs (public, with pagination).
* `GET /jobs/my-jobs`: Recruiter lists their own postings (requires Recruiter auth).
* `GET /jobs/{job_id}`: View single job details (includes `has_applied` status if candidate is logged in).
* `POST /jobs/`: Create a job opening with criteria and screening questions (requires Recruiter auth).
* `PATCH /jobs/{job_id}`: Partial update of a job posting (owner only).
* `DELETE /jobs/{job_id}`: Deactivate/close a job posting (owner only).

### File Uploads (`/upload`)
* `POST /upload/resume`: Candidate uploads PDF/DOCX (max 5 MB). File saved in `uploads/resumes/` with unique UUID.
* `POST /upload/logo`: Recruiter uploads company logo (max 1 MB).

### Applications (`/applications`)
* `POST /applications/`: Candidate applies to a job. Validates job existence, verifies active status, blocks duplicates, validates required screening questions, creates application, and automatically triggers background AI ranking.
* `GET /applications/my-applications`: Candidate views their applications with status history.
* `GET /applications/job/{job_id}`: Recruiter views all applications for their job.
* `PUT /applications/{application_id}/status`: Recruiter updates status (`applied` $\rightarrow$ `interview` $\rightarrow$ `offer` $\rightarrow$ `rejected`).

### AI Ranking & Matching (`/ranking`)
* `GET /ranking/job/{job_id}`: Recruiter gets all applications ranked by `final_match_score` descending with matched/missing skills and rank numbers.
* `GET /ranking/application/{app_id}/analysis`: Recruiter gets complete AI breakdown (scores across all 6 criteria, candidate details, eligibility status, and metadata).
* `POST /ranking/application/{app_id}/reprocess`: Re-evaluates ranking for a single application.
* `POST /ranking/job/{job_id}/reprocess`: Re-evaluates rankings for all candidates under a job opening.

---

## 5. Dataset Batch Processing Subsystem

The batch processing subsystem enables offline evaluation on large resume datasets without altering production MongoDB state.

### How to Run:
```bash
# Process a 20-resume sample from specific categories:
python run_batch.py --categories "Data Science,Python Developer" --limit 20

# Process full dataset into structured JSONs and generate report:
python run_batch.py --dataset-dir ../resume_data --output-dir data/processed
```

### Outputs Generated:
1. **`data/processed/<category>/<resume_id>.json`**: The complete strongly-typed `ParsedResume` dictionary for every parsed resume.
2. **`data/processed/batch_report.json`**: Aggregate analytics including:
   * Total processed, success count, failure count, success rate.
   * Total & average duration per resume.
   * Section extraction success percentages (`has_name`, `has_email`, `has_phone`, `has_skills`, `has_experience`, `has_projects`, `has_education`, `has_summary`).
   * Average counts of skills, experience entries, and projects per resume.
   * Top 15 most frequent skills across the dataset.
   * Category breakdown and failure reason distributions.

---

## 6. Viva / Project Review Quick Reference

| Question | Technical Answer |
|---|---|
| **How does resume parsing work?** | Hybrid pipeline: `pdfplumber` extracts text streams; scanned/image PDFs trigger OCR via `pypdfium2` and `RapidOCR`; regex extracts section boundaries; spaCy NER extracts personal entities; canonical taxonomy normalizes 120+ skills. |
| **Why not embed the whole resume at once?** | Single-vector embeddings suffer from information dilution across long documents. We generate separate representations for Experience and Projects, and compare them against Job Requirements and Responsibilities respectively. |
| **How do you prevent duplicate parsing overhead?** | Resumes are parsed once and stored in the `parsed_resumes` collection keyed by `candidate_id`. When a candidate applies to multiple jobs, the existing structured profile is reused. |
| **What is the ranking algorithm?** | `hybrid-baseline-v1` — a weighted multi-criteria decision model aggregating 6 normalized features ($S_{\text{skills}}$, $S_{\text{semantic}}$, $S_{\text{exp}}$, $S_{\text{proj}}$, $S_{\text{edu}}$, $S_{\text{screen}}$) with configurable weights. |
| **How is the system research-ready?** | Feature extraction is decoupled from scoring. The extracted 6-dimensional feature vector can be directly piped into Learning-to-Rank models (e.g. LightGBM LambdaMART, RankNet) or compared against TF-IDF / BM25 baselines. |
