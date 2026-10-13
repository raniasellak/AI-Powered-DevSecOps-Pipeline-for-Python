from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Retourne l'empreinte Argon2 (avec sel aleatoire integre)."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Compare un mot de passe a son empreinte (utilise a l'etape login)."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False