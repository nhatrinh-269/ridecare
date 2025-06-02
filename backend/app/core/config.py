# backend/app/core/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "RideCare API"
    PROJECT_VERSION: str = "1.0.0"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:ridecaredb@localhost:5432/ridecaredb_local"
    )

settings = Settings()