# app/api/routers/admin_users.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.admin_user_repository import AdminUserRepository
from app.schemas.admin_user import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    AdminUserLogin
)
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/admin-users", tags=["Admin Users"])


@router.post("/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
        user_data: AdminUserCreate,
        db: Session = Depends(get_db)
):
    """Create new admin user"""
    # Check if username already exists
    if AdminUserRepository.exists_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    if AdminUserRepository.exists_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    user = AdminUserRepository.create(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    return user


@router.post("/login", response_model=AdminUserResponse)
def login(
        login_data: AdminUserLogin,
        db: Session = Depends(get_db)
):
    """Authenticate admin user"""
    user = AdminUserRepository.authenticate(
        db=db,
        username=login_data.username,
        password=login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Update last login
    AdminUserRepository.update_last_login(db, user.id)
    return user


@router.get("/", response_model=PaginatedResponse[AdminUserResponse])
def get_admin_users(
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        db: Session = Depends(get_db)
):
    """Get all admin users"""
    users = AdminUserRepository.get_all(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )
    total = AdminUserRepository.count(db=db, active_only=active_only)

    return PaginatedResponse(
        items=users,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=((total - 1) // limit) + 1 if total > 0 else 0,
        has_next=(skip + limit) < total,
        has_prev=skip > 0
    )


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_admin_user(
        user_id: int,
        db: Session = Depends(get_db)
):
    """Get admin user by ID"""
    user = AdminUserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
        user_id: int,
        user_data: AdminUserUpdate,
        db: Session = Depends(get_db)
):
    """Update admin user"""
    # Check if user exists
    existing_user = AdminUserRepository.get_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check username uniqueness if being updated
    if user_data.username and user_data.username != existing_user.username:
        if AdminUserRepository.exists_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

    # Check email uniqueness if being updated
    if user_data.email and user_data.email != existing_user.email:
        if AdminUserRepository.exists_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

    update_data = user_data.model_dump(exclude_unset=True)
    user = AdminUserRepository.update(db, user_id, **update_data)
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_admin_user(
        user_id: int,
        db: Session = Depends(get_db)
):
    """Delete admin user"""
    if not AdminUserRepository.delete(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return MessageResponse(message="User deleted successfully")

