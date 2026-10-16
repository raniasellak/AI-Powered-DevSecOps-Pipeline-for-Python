from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from . import models, schemas
from .deps import get_current_user, require_roles
from .refresh import issue_refresh_token, revoke_refresh_family, rotate_refresh_token
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
    email = form.username.lower()
    user = db.scalar(select(models.User).where(models.User.email == email))

    password_hash = user.password_hash if user else DUMMY_HASH
    password_ok = len(form.password) <= 128 and verify_password(
        form.password, password_hash
    )

    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Identifiants invalides.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh = issue_refresh_token(db, user.id)
    db.commit()
    return schemas.Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=refresh,
    )


@router.post("/refresh", response_model=schemas.Token)
def refresh(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    result = rotate_refresh_token(db, data.refresh_token)
    if result is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Jeton de rafraichissement invalide."
        )

    user_id, new_refresh = result
    user = db.get(models.User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Jeton de rafraichissement invalide."
        )
    return schemas.Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    # Meme reponse que le jeton existe ou non : aucune information donnee
    revoke_refresh_family(db, data.refresh_token)


@router.get("/me", response_model=schemas.UserRead)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.get("/admin/ping")
def admin_ping(user: models.User = Depends(require_roles("admin"))):
    return {"message": "Bienvenue, admin."}