import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "RideCare API"
    PROJECT_VERSION: str = "1.0.0"

    # Database
    DB_USER: str = os.getenv("DB_USER", "admin")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "ridecaredb")
    DB_HOST: str = os.getenv("DB_HOST", "192.168.1.15")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306") or 3306)
    DB_NAME: str = os.getenv("DB_NAME", "ridecaredb")
    DATABASE_URL: str = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

settings = Settings()
