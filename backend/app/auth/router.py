from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from . import models, schemas
from .deps import get_current_user, require_roles
from .security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)

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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Inscription impossible.")
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Le formulaire OAuth2 s'appelle "username" : chez nous, c'est l'email.
    email = form.username.lower()
    user = db.scalar(select(models.User).where(models.User.email == email))

    # Meme travail (une verification Argon2) que le compte existe ou non
    password_hash = user.password_hash if user else DUMMY_HASH
    password_ok = len(form.password) <= 128 and verify_password(
        form.password, password_hash
    )

    # Meme message pour : email inconnu, mauvais mot de passe, compte inactif
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Identifiants invalides.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return schemas.Token(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=schemas.UserRead)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.get("/admin/ping")
def admin_ping(user: models.User = Depends(require_roles("admin"))):
    # Endpoint temporaire pour prouver que le RBAC fonctionne
    return {"message": "Bienvenue, admin."}