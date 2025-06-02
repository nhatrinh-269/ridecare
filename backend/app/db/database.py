# backend/app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Đảm bảo import đúng Settings class

# Tạo engine kết nối đến PostgreSQL
# Chuỗi kết nối từ settings.DATABASE_URL phải là 'postgresql://...'
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # Bật True nếu muốn log câu SQL để debug
)

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các model ORM
Base = declarative_base()


# Dependency để dùng trong route hoặc xử lý logic
def get_db():
    """
    Dependency inject cho FastAPI route: cung cấp DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()