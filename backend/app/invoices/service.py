"""
Services P3 :
  - génération de facture depuis une mission
  - lien signé à usage limité
  - ancrage hash blockchain (sandbox)
  - journal d'audit append-only
"""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from .models import AuditLog, BlockchainProof, Invoice, Mission

# Durée de validité du lien de paiement
SIGNED_LINK_TTL_HOURS = 48


# ---------------------------------------------------------------------------
# Numérotation des factures
# ---------------------------------------------------------------------------

def _next_invoice_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Invoice).filter(
        Invoice.number.like(f"INV-{year}-%")
    ).count()
    return f"INV-{year}-{count + 1:04d}"


# ---------------------------------------------------------------------------
# Génération de facture
# ---------------------------------------------------------------------------

def create_invoice_for_mission(mission_id: uuid.UUID, db: Session) -> Invoice:
    """
    Génère une facture depuis une mission confirmée.
    - Le montant est copié depuis la mission et ne peut pas être modifié.
    - Une seule facture par mission (contrainte unique en base).
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise ValueError("Mission introuvable")
    if mission.status != "confirmed":
        raise ValueError("La mission doit être confirmée avant de facturer")

    existing = db.query(Invoice).filter(Invoice.mission_id == mission_id).first()
    if existing:
        raise ValueError("Une facture existe déjà pour cette mission")

    invoice = Invoice(
        mission_id=mission.id,
        number=_next_invoice_number(db),
        amount=mission.amount,   # montant figé
    )
    invoice.content_hash = invoice.compute_hash()
    db.add(invoice)

    mission.status = "invoiced"
    db.commit()
    db.refresh(invoice)
    return invoice


# ---------------------------------------------------------------------------
# Lien signé à usage limité
# ---------------------------------------------------------------------------

def _sign_token(invoice_id: uuid.UUID, expires_at: datetime) -> str:
    """Génère un token HMAC signé avec la clé JWT."""
    payload = f"{invoice_id}|{expires_at.isoformat()}"
    sig = hmac.new(
        settings.jwt_secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    raw = secrets.token_urlsafe(16)
    return f"{raw}.{sig}"


def generate_pay_link(invoice_id: uuid.UUID, base_url: str, db: Session) -> dict:
    """
    Crée un token signé à usage unique valable SIGNED_LINK_TTL_HOURS heures.
    Retourne l'URL de paiement et la date d'expiration.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError("Facture introuvable")
    if invoice.token_used:
        raise ValueError("Le lien de paiement a déjà été utilisé")

    expires_at = datetime.now(timezone.utc) + timedelta(hours=SIGNED_LINK_TTL_HOURS)
    token = _sign_token(invoice_id, expires_at)

    invoice.signed_token = token
    invoice.token_expires_at = expires_at
    db.commit()

    return {
        "pay_url": f"{base_url}/pay/{token}",
        "expires_at": expires_at,
    }


def consume_pay_link(token: str, db: Session) -> Invoice:
    """
    Valide et consomme un lien de paiement.
    - Vérifie que le token existe, n'est pas expiré et n'a pas déjà été utilisé.
    """
    invoice = db.query(Invoice).filter(Invoice.signed_token == token).first()
    if not invoice:
        raise ValueError("Lien invalide")
    if invoice.token_used:
        raise ValueError("Lien déjà utilisé")
    if invoice.token_expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None):
        raise ValueError("Lien expiré")

    invoice.token_used = True
    db.commit()
    db.refresh(invoice)
    return invoice


# ---------------------------------------------------------------------------
# Ancrage blockchain (sandbox)
# ---------------------------------------------------------------------------

def anchor_to_blockchain(invoice: Invoice, db: Session) -> BlockchainProof:
    """
    Ancre le hash de la facture sur la blockchain (simulé en sandbox).
    En production, remplacer par un appel à un nœud Ethereum/IPFS.
    """
    existing = db.query(BlockchainProof).filter(
        BlockchainProof.invoice_id == invoice.id
    ).first()
    if existing:
        return existing

    # Sandbox : tx_hash = SHA-256(content_hash + timestamp)
    raw = f"{invoice.content_hash}|{datetime.now(timezone.utc).isoformat()}"
    tx_hash = hashlib.sha256(raw.encode()).hexdigest()

    proof = BlockchainProof(
        invoice_id=invoice.id,
        content_hash=invoice.content_hash,
        tx_hash=tx_hash,
    )
    db.add(proof)
    db.commit()
    db.refresh(proof)
    return proof


# ---------------------------------------------------------------------------
# Journal d'audit append-only
# ---------------------------------------------------------------------------

def log_action(
    actor_id: uuid.UUID,
    action: str,
    resource: str,
    resource_id: str,
    db: Session,
    detail: str | None = None,
) -> None:
    """Ajoute une entrée au journal d'audit — jamais de mise à jour ni suppression."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        detail=detail,
    )
    db.add(entry)
    db.commit()
