import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # montant figé à la création — ne peut plus changer
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    freelance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    # pending | delivered | confirmed | invoiced | paid
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    mission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("missions.id"), unique=True, index=True
    )
    number: Mapped[str] = mapped_column(String(30), unique=True)  # ex: INV-2024-0001
    amount: Mapped[float] = mapped_column(Numeric(10, 2))         # copié depuis la mission
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.20)
    # hash SHA-256 du contenu de la facture
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    # token signé pour le lien de paiement à usage limité
    signed_token: Mapped[str] = mapped_column(String(256), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def compute_hash(self) -> str:
        """Calcule le hash SHA-256 du contenu de la facture."""
        raw = f"{self.id}|{self.mission_id}|{self.number}|{self.amount}|{self.created_at}"
        return hashlib.sha256(raw.encode()).hexdigest()


class AuditLog(Base):
    """Journal d'audit en ajout seul — aucune mise à jour ni suppression."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))   # ex: invoice.created, mission.paid
    resource: Mapped[str] = mapped_column(String(50))  # ex: invoice, mission
    resource_id: Mapped[str] = mapped_column(String(36))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BlockchainProof(Base):
    """Preuve d'ancrage du hash d'une facture (simulé en sandbox)."""
    __tablename__ = "blockchain_proofs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id"), unique=True, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    # en prod : tx_hash de la blockchain ; en sandbox : hash simulé
    tx_hash: Mapped[str] = mapped_column(String(128))
    anchored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
