import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MissionCreate(BaseModel):
    title: str
    description: str | None = None
    amount: float
    client_id: uuid.UUID


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    amount: float
    status: str
    freelance_id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    delivered_at: datetime | None
    paid_at: datetime | None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mission_id: uuid.UUID
    number: str
    amount: float
    tax_rate: float
    content_hash: str | None
    token_used: bool
    created_at: datetime


class InvoicePayLink(BaseModel):
    """Lien signé à usage limité envoyé au payeur."""
    pay_url: str
    expires_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    resource: str
    resource_id: str
    detail: str | None
    created_at: datetime


class BlockchainProofRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    content_hash: str
    tx_hash: str
    anchored_at: datetime


class HistoryEntry(BaseModel):
    """Une entrée dans l'historique du freelance."""
    mission: MissionRead
    invoice: InvoiceRead | None
    blockchain_proof: BlockchainProofRead | None
