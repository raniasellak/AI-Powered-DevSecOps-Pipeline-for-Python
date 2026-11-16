"""Briques de sécurité du module factures : tokens, hash, chaîne d'audit."""
import hashlib
import json
import secrets
from datetime import datetime, timezone

GENESIS_HASH = "GENESIS"  # "prev_hash" de la toute première ligne du journal


def generate_token() -> str:
    """Token aléatoire imprévisible pour le lien de paiement."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """On stocke seulement l'empreinte du token, jamais le token lui-même."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Empreinte d'un fichier (par exemple le PDF de la facture)."""
    return hashlib.sha256(data).hexdigest()


def amount_matches(invoice_cents: int, mission_cents: int) -> bool:
    """Règle du README : la facture doit être EXACTEMENT égale à la mission."""
    return invoice_cents == mission_cents


def link_is_usable(expires_at: datetime, max_uses: int, used_count: int,
                   now: datetime | None = None) -> bool:
    """Un lien est valide s'il n'est pas expiré et pas déjà épuisé."""
    now = now or datetime.now(timezone.utc)
    return now < expires_at and used_count < max_uses


def compute_audit_hash(prev_hash: str, event: str, payload: dict) -> str:
    """Empreinte d'une ligne du journal, liée à l'empreinte de la ligne précédente."""
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{prev_hash}|{event}|{data}".encode("utf-8")).hexdigest()


def verify_chain(entries: list[dict]) -> bool:
    """Recalcule toute la chaîne. False si une ligne a été modifiée."""
    prev = GENESIS_HASH
    for e in entries:
        if e["prev_hash"] != prev:
            return False
        if compute_audit_hash(prev, e["event"], e["payload"]) != e["hash"]:
            return False
        prev = e["hash"]
    return True