from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from . import models, schemas
from .security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()

    exists = db.scalar(select(models.User).where(models.User.email == email))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Inscription impossible.")

    user = models.User(
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # deux inscriptions simultanees avec le meme email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Inscription impossible.")
    db.refresh(user)
    return user