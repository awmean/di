from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.admin_users.repository import AdminUserRepository
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_admin(login='adm1n', password='testerluce'):
    AdminUserRepository.create(
        db=SessionLocal,
        username=login,
        email='test@example.ru',
        password=password
    )
