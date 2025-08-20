from datetime import datetime
from typing import Sequence, Optional

from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import AdminUser

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminUserRepository:
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create(db: Session, username: str, email: str, password: str,
               is_active: bool = True) -> AdminUser:
        """Create new admin user with hashed password"""
        password_hash = AdminUserRepository._hash_password(password)

        user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_with_hash(db: Session, username: str, email: str, password_hash: str,
                         is_active: bool = True) -> AdminUser:
        """Create new admin user with pre-hashed password (for migrations/admin creation)"""
        user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate user with username/email and password"""
        # Try to find user by username or email
        user = AdminUserRepository.get_by_username(db, username)
        if not user:
            user = AdminUserRepository.get_by_email(db, username)

        if not user or not user.is_active:
            return None

        if not AdminUserRepository.verify_password(password, str(user.password_hash)):
            return None

        return user

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[AdminUser]:
        """Get admin user by ID"""
        return db.get(AdminUser, user_id)

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[AdminUser]:
        """Get admin user by username"""
        stmt = select(AdminUser).where(AdminUser.username == username)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[AdminUser]:
        """Get admin user by email"""
        stmt = select(AdminUser).where(AdminUser.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100,
                active_only: bool = False) -> Sequence[AdminUser]:
        """Get all admin users"""
        stmt = select(AdminUser)

        if active_only:
            stmt = stmt.where(AdminUser.is_active)

        stmt = stmt.order_by(AdminUser.username).offset(skip).limit(limit)
        return db.scalars(stmt).all()

    @staticmethod
    def update(db: Session, user_id: int, **kwargs) -> Optional[AdminUser]:
        """Update admin user"""
        user = db.get(AdminUser, user_id)
        if not user:
            return None

        # Handle password update specially
        if 'password' in kwargs:
            kwargs['password_hash'] = AdminUserRepository._hash_password(kwargs.pop('password'))

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> Optional[AdminUser]:
        """Update user password"""
        user = db.get(AdminUser, user_id)
        if not user:
            return None

        user.password_hash = AdminUserRepository._hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_last_login(db: Session, user_id: int) -> Optional[AdminUser]:
        """Update last login timestamp"""
        user = db.get(AdminUser, user_id)
        if not user:
            return None

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """Delete admin user"""
        user = db.get(AdminUser, user_id)
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def count(db: Session, active_only: bool = False) -> int:
        """Count admin users"""
        stmt = select(func.count(AdminUser.id))

        if active_only:
            stmt = stmt.where(AdminUser.is_active)

        return db.execute(stmt).scalar() or 0

    @staticmethod
    def exists_by_username(db: Session, username: str) -> bool:
        """Check if username already exists"""
        stmt = select(AdminUser.id).where(AdminUser.username == username)
        return db.execute(stmt).scalar() is not None

    @staticmethod
    def exists_by_email(db: Session, email: str) -> bool:
        """Check if email already exists"""
        stmt = select(AdminUser.id).where(AdminUser.email == email)
        return db.execute(stmt).scalar() is not None
