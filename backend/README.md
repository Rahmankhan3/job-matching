# Job Tracker - Backend

This is the backend repository for the Job Tracking & Matching system. It provides a robust, asynchronous RESTful API built with FastAPI and MongoDB to manage job postings, job applications, resumes, candidate profiles, and recruiter profiles.

## 🚀 Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Language:** Python 3.9+
- **Database:** MongoDB (via [PyMongo](https://pymongo.readthedocs.io/))
- **Data Validation:** Pydantic
- **Authentication:** JWT (JSON Web Tokens), Argon2 for password hashing
- **Server:** Uvicorn

## 🛠️ Key Features

- **Authentication & Authorization**: Secure JWT-based registration and login system with Role-Based Access Control (Candidate vs. Recruiter).
- **Candidate Profiles**: Candidates can build out profiles, upload their resumes, and manage their job applications.
- **Recruiter Profiles**: Companies/Recruiters can create profiles, upload company logos, and post new jobs.
- **Job Management**: Recruiters can create, read, update, and manage job listings. Candidates can fetch and browse available jobs.
- **Application Tracking**: Candidates can apply for jobs; Recruiters can track, view, and manage applicants based on specific job postings.
- **File Uploads**: Static file serving implementation for resume and logo uploads natively handled within the backend.

## 📁 Project Structure

```text
backend/
├── app/
│   ├── config.py             # Environment configurations
│   ├── database.py           # MongoDB connection and index setups
│   ├── main.py               # FastAPI application entry point
│   ├── middleware/           # Custom middlewares
│   ├── models/               # Pydantic data models & schema validation
│   ├── routes/               # API endpoints (auth, jobs, applications, etc.)
│   ├── services/             # Core business logic
│   ├── uploads/              # Static directory for resumes and logos
│   └── utils/                # Helper functions (JWT, passwords)
├── .env.example              # Sample environment variables
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## ⚙️ Prerequisites

- **Python 3.9+** installed on your machine.
- **MongoDB** running locally (`localhost:27017`) or a connected MongoDB Atlas cluster URI.

## 💻 Local Setup Instructions

1. **Clone the repository** (or navigate to the backend directory):
   ```bash
   git clone https://github.com/Rahmankhan3/job-matching.git
   cd job-matching/backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Environment Variables**:
   Create a `.env` file in the `backend/` directory by copying `.env.example`:
   ```bash
   # On Windows
   copy .env.example .env
   
   # On macOS/Linux
   cp .env.example .env
   ```
   *Make sure to update the internal variables in `.env` like `SECRET_KEY`, `MONGODB_URL`, and `DATABASE_NAME` if required.*

6. **Run the Development Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**:
   - The application will be running at: `http://localhost:8000`
   - **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
   - **Alternative API Docs (ReDoc)**: `http://localhost:8000/redoc`

## 🔀 Core API Routes

- `POST /auth/register` - Create a new user account.
- `POST /auth/login` - Authenticate a user and receive a JWT token.
- `GET /jobs/` - Fetch available job listings.
- `POST /jobs/` - Create a new job posting (Recruiter only).
- `POST /applications/` - Submit a job application (Candidate only).
- `GET /applications/{job_id}` - View applications for a specific job (Recruiter only).
- `POST /upload/resume` - Upload a candidate resume securely.
