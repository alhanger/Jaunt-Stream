# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import User
from ..core.auth import get_current_user

router = APIRouter()

@router.post("/register")
async def register_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new user after successful Auth0 authentication
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.id == current_user["sub"]).first()
    if existing_user:
        return {"message": "User already registered"}

    # Create new user
    new_user = User(
        id=current_user["sub"],
        email=current_user.get("email", "")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}

@router.get("/me")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile
    """
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "last_login": user.last_login
    }