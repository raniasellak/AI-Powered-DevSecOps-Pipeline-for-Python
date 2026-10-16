import uuid
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from ..config import settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Retourne l'empreinte Argon2 (avec sel aleatoire integre)."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Compare un mot de passe a son empreinte."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


# Empreinte factice : permet de faire le meme travail quand l'email
# n'existe pas, pour ne pas reveler par le temps de reponse qu'un compte existe.
DUMMY_HASH = hash_password("mot-de-passe-factice-pour-uniformiser-le-temps")


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": uuid.uuid4().hex,  # identifiant unique (revocation plus tard)
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],  # liste fixe : jamais celle du jeton
        options={"require": ["exp", "sub", "iat"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("mauvais type de jeton")
    return payload