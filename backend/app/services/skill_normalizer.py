"""
Canonical skill normalization for consistent matching.

Maps common aliases, abbreviations, and variations to a single canonical form.
The mapping is intentionally maintained as a flat dictionary — easy to extend,
easy to inspect, and no risk of over-engineering.
"""
import re
from typing import List, Dict, Set

# ── Canonical Mapping ─────────────────────────────────────────────────────────
# Keys are lowercased aliases; values are the preferred display form.
# When adding new entries: add the canonical form mapping to itself so it
# appears in KNOWN_SKILLS, then add all known aliases pointing to the same form.

CANONICAL_SKILLS: Dict[str, str] = {
    # Python ecosystem
    "python": "Python", "python3": "Python", "python 3": "Python",
    "django": "Django", "flask": "Flask",
    "fastapi": "FastAPI", "fast api": "FastAPI", "fast-api": "FastAPI",
    "pandas": "Pandas", "numpy": "NumPy",
    "scikit-learn": "Scikit-learn", "sklearn": "Scikit-learn",
    "matplotlib": "Matplotlib", "seaborn": "Seaborn",
    "opencv": "OpenCV", "open cv": "OpenCV",
    "pytest": "Pytest", "unittest": "Unittest",
    "celery": "Celery", "scrapy": "Scrapy", "beautifulsoup": "BeautifulSoup",
    "pydantic": "Pydantic", "sqlalchemy": "SQLAlchemy",

    # JavaScript / TypeScript ecosystem
    "javascript": "JavaScript", "js": "JavaScript",
    "typescript": "TypeScript", "ts": "TypeScript",
    "react": "React", "reactjs": "React", "react.js": "React", "react js": "React",
    "next.js": "Next.js", "nextjs": "Next.js", "next js": "Next.js",
    "angular": "Angular", "angularjs": "Angular", "angular.js": "Angular",
    "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js", "vue js": "Vue.js",
    "node.js": "Node.js", "nodejs": "Node.js", "node js": "Node.js", "node": "Node.js",
    "express": "Express.js", "expressjs": "Express.js", "express.js": "Express.js",
    "jquery": "jQuery", "redux": "Redux",
    "jest": "Jest", "mocha": "Mocha", "webpack": "Webpack", "vite": "Vite",
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS", "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",

    # Java ecosystem
    "java": "Java",
    "spring": "Spring", "spring boot": "Spring Boot", "springboot": "Spring Boot",
    "hibernate": "Hibernate", "maven": "Maven", "gradle": "Gradle",

    # C / C++ / C#
    "c": "C", "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#", "c sharp": "C#",
    ".net": ".NET", "dotnet": ".NET", "asp.net": "ASP.NET",

    # Other languages
    "golang": "Go", "go": "Go",
    "rust": "Rust", "php": "PHP", "ruby": "Ruby",
    "r": "R", "matlab": "MATLAB",
    "kotlin": "Kotlin", "swift": "Swift", "dart": "Dart",
    "scala": "Scala", "perl": "Perl", "haskell": "Haskell",
    "shell": "Shell", "bash": "Bash", "powershell": "PowerShell",

    # Mobile
    "flutter": "Flutter",
    "react native": "React Native", "react-native": "React Native",
    "android": "Android", "ios": "iOS",

    # Databases
    "mongodb": "MongoDB", "mongo": "MongoDB", "mongo db": "MongoDB",
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mysql": "MySQL", "mariadb": "MariaDB",
    "redis": "Redis", "sqlite": "SQLite",
    "firebase": "Firebase", "firestore": "Firestore",
    "cassandra": "Cassandra", "dynamodb": "DynamoDB",
    "sql": "SQL", "nosql": "NoSQL",
    "elasticsearch": "Elasticsearch", "elastic search": "Elasticsearch",
    "neo4j": "Neo4j",

    # Cloud & DevOps
    "aws": "AWS", "amazon web services": "AWS",
    "azure": "Azure", "microsoft azure": "Azure",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "ansible": "Ansible",
    "jenkins": "Jenkins", "github actions": "GitHub Actions",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "nginx": "Nginx", "apache": "Apache",
    "linux": "Linux", "ubuntu": "Ubuntu",
    "heroku": "Heroku", "vercel": "Vercel", "netlify": "Netlify",

    # AI / ML / Data
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "machine-learning": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence", "ai": "Artificial Intelligence",
    "nlp": "NLP", "natural language processing": "NLP",
    "computer vision": "Computer Vision", "cv": "Computer Vision",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "keras": "Keras", "hugging face": "Hugging Face", "huggingface": "Hugging Face",
    "langchain": "LangChain",
    "data science": "Data Science", "data analysis": "Data Analysis",
    "data engineering": "Data Engineering",
    "power bi": "Power BI", "powerbi": "Power BI",
    "tableau": "Tableau", "excel": "Excel",
    "spacy": "spaCy",

    # Web / API
    "html": "HTML", "html5": "HTML",
    "css": "CSS", "css3": "CSS",
    "sass": "Sass", "scss": "Sass", "less": "LESS",
    "rest api": "REST API", "rest": "REST API", "restful": "REST API",
    "graphql": "GraphQL", "grpc": "gRPC",
    "websocket": "WebSocket", "websockets": "WebSocket",

    # Tools & Practices
    "git": "Git", "github": "GitHub", "gitlab": "GitLab", "bitbucket": "Bitbucket",
    "jira": "Jira", "confluence": "Confluence",
    "figma": "Figma", "adobe xd": "Adobe XD",
    "ui/ux": "UI/UX", "ui ux": "UI/UX",
    "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
    "microservices": "Microservices",
    "cloud computing": "Cloud Computing",
    "selenium": "Selenium", "cypress": "Cypress",
    "postman": "Postman", "swagger": "Swagger",

    # Blockchain
    "blockchain": "Blockchain", "solidity": "Solidity",
    "web3": "Web3", "ethereum": "Ethereum",
}

# Pre-built set of all canonical skill names (for taxonomy-based extraction)
KNOWN_SKILLS: Set[str] = set(CANONICAL_SKILLS.values())

# Pre-compiled patterns for taxonomy-based extraction from free text.
# Sorted by length descending so longer matches take priority
# (e.g., "machine learning" matches before "machine").
_TAXONOMY_ENTRIES = sorted(CANONICAL_SKILLS.keys(), key=len, reverse=True)
_SKILL_PATTERNS = [
    (alias, CANONICAL_SKILLS[alias], re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE))
    for alias in _TAXONOMY_ENTRIES
]


def normalize_skill(raw: str) -> str:
    """Normalize a single skill string to its canonical form."""
    key = raw.strip().lower()
    return CANONICAL_SKILLS.get(key, raw.strip())


def normalize_skills(raw_list: List[str]) -> List[str]:
    """Normalize a list of skills, deduplicate, and sort."""
    seen = set()
    result = []
    for raw in raw_list:
        canonical = normalize_skill(raw)
        if canonical.lower() not in seen:
            seen.add(canonical.lower())
            result.append(canonical)
    return sorted(result)


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known skills from free text using taxonomy patterns."""
    found = set()
    text_lower = text.lower()
    for _alias, canonical, pattern in _SKILL_PATTERNS:
        if canonical.lower() not in found and pattern.search(text_lower):
            found.add(canonical.lower())
    return sorted(CANONICAL_SKILLS.get(s, s) for s in found)


def extract_skills_with_evidence(text: str, source_label: str) -> List[dict]:
    """
    Extract skills from text and tag each with its source.
    Returns list of {"skill": "Python", "source": "project:0"}.
    """
    results = []
    text_lower = text.lower()
    seen = set()
    for _alias, canonical, pattern in _SKILL_PATTERNS:
        if canonical.lower() not in seen and pattern.search(text_lower):
            seen.add(canonical.lower())
            results.append({"skill": canonical, "source": source_label})
    return results
