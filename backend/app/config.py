from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    APP_NAME: str = "Job Application Tracker"
    DEBUG: bool = True

    # ── AI / NLP Configuration ────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    RANKING_MODEL_VERSION: str = "hybrid-baseline-v1"
    PARSER_VERSION: str = "1.0.0"

    # Dataset directory for batch experiments (set via .env when needed)
    DATASET_DIR: str = ""

    # Initial baseline ranking weights — subject to future experimentation.
    # These are NOT scientifically validated; they are reasonable starting
    # points derived from domain intuition.
    RANKING_WEIGHT_SKILLS: float = 0.25
    RANKING_WEIGHT_SEMANTIC: float = 0.20
    RANKING_WEIGHT_EXPERIENCE: float = 0.25
    RANKING_WEIGHT_PROJECTS: float = 0.15
    RANKING_WEIGHT_EDUCATION: float = 0.05
    RANKING_WEIGHT_SCREENING: float = 0.10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

