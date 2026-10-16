import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import settings
from . import models


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    # SQLite ne conserve pas le fuseau horaire : on le remet.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_refresh_token(
    db: Session, user_id: uuid.UUID, family_id: uuid.UUID | None = None
) -> str:
    """Cree un refresh token et retourne sa valeur en clair (une seule fois).
    L'appelant doit faire db.commit()."""
    raw = secrets.token_urlsafe(48)
    db.add(
        models.RefreshToken(
            user_id=user_id,
            family_id=family_id or uuid.uuid4(),
            token_hash=_hash(raw),
            expires_at=_now() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return raw


def _revoke_family(db: Session, family_id: uuid.UUID) -> None:
    db.execute(
        update(models.RefreshToken)
        .where(
            models.RefreshToken.family_id == family_id,
            models.RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=_now())
    )


def rotate_refresh_token(db: Session, raw: str) -> tuple[uuid.UUID, str] | None:
    """Verifie le jeton, le revoque, en emet un nouveau.
    Retourne (user_id, nouveau_jeton) ou None si invalide."""
    row = db.scalar(
        select(models.RefreshToken).where(
            models.RefreshToken.token_hash == _hash(raw)
        )
    )
    if row is None:
        return None

    if row.revoked_at is not None:
        # Rejeu d'un jeton deja utilise : vol probable -> on coupe la famille
        _revoke_family(db, row.family_id)
        db.commit()
        return None

    if _aware(row.expires_at) < _now():
        return None

    row.revoked_at = _now()
    new_raw = issue_refresh_token(db, row.user_id, row.family_id)
    db.commit()
    return row.user_id, new_raw


def revoke_refresh_family(db: Session, raw: str) -> None:
    """Deconnexion : revoque toute la famille. Silencieux si le jeton est inconnu."""
    row = db.scalar(
        select(models.RefreshToken).where(
            models.RefreshToken.token_hash == _hash(raw)
        )
    )
    if row is not None:
        _revoke_family(db, row.family_id)
        db.commit()