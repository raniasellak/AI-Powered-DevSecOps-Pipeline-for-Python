import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..auth.models import User
from ..database import get_db
from .models import AuditLog, BlockchainProof, Invoice, Mission
from .pdf import generate_invoice_pdf
from .schemas import (
    AuditLogRead,
    BlockchainProofRead,
    HistoryEntry,
    InvoicePayLink,
    InvoiceRead,
    MissionCreate,
    MissionRead,
)
from .service import (
    anchor_to_blockchain,
    consume_pay_link,
    create_invoice_for_mission,
    generate_pay_link,
    log_action,
)

router = APIRouter(prefix="/v1", tags=["invoices"])


# ---------------------------------------------------------------------------
# Missions
# ---------------------------------------------------------------------------

@router.post("/missions", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
def create_mission(
    body: MissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée une mission (montant figé dès la création)."""
    mission = Mission(
        title=body.title,
        description=body.description,
        amount=body.amount,
        freelance_id=current_user.id,
        client_id=body.client_id,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    log_action(current_user.id, "mission.created", "mission", str(mission.id), db)
    return mission


@router.patch("/missions/{mission_id}/deliver", response_model=MissionRead)
def deliver_mission(
    mission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Le freelance marque la mission comme livrée."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    if mission.freelance_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Statut invalide")

    from datetime import datetime, timezone
    mission.status = "delivered"
    mission.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mission)
    log_action(current_user.id, "mission.delivered", "mission", str(mission_id), db)
    return mission


@router.patch("/missions/{mission_id}/confirm", response_model=MissionRead)
def confirm_mission(
    mission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Le client confirme la livraison."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    if mission.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    if mission.status != "delivered":
        raise HTTPException(status_code=400, detail="La mission n'est pas encore livrée")

    mission.status = "confirmed"
    db.commit()
    db.refresh(mission)
    log_action(current_user.id, "mission.confirmed", "mission", str(mission_id), db)
    return mission


# ---------------------------------------------------------------------------
# Factures
# ---------------------------------------------------------------------------

@router.post("/missions/{mission_id}/invoice", response_model=InvoiceRead, status_code=201)
def generate_invoice(
    mission_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Génère la facture d'une mission confirmée.
    Le montant est verrouillé sur celui de la mission.
    Ancre automatiquement le hash sur la blockchain.
    """
    try:
        invoice = create_invoice_for_mission(mission_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    anchor_to_blockchain(invoice, db)
    log_action(current_user.id, "invoice.created", "invoice", str(invoice.id), db,
               detail=f"number={invoice.number} amount={invoice.amount}")
    return invoice


@router.post("/invoices/{invoice_id}/pay-link", response_model=InvoicePayLink)
def get_pay_link(
    invoice_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Génère un lien de paiement signé à usage unique (valable 48h)."""
    base_url = str(request.base_url).rstrip("/")
    try:
        result = generate_pay_link(invoice_id, base_url, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_action(current_user.id, "invoice.pay_link_generated", "invoice", str(invoice_id), db)
    return result


@router.get("/pay/{token}", response_model=InvoiceRead)
def use_pay_link(token: str, db: Session = Depends(get_db)):
    """
    Consomme un lien de paiement signé.
    - Refuse si expiré ou déjà utilisé.
    """
    try:
        invoice = consume_pay_link(token, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return invoice


@router.get("/invoices/{invoice_id}/proof", response_model=BlockchainProofRead)
def get_blockchain_proof(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retourne la preuve blockchain d'une facture."""
    proof = db.query(BlockchainProof).filter(
        BlockchainProof.invoice_id == invoice_id
    ).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Preuve introuvable")
    return proof


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Télécharge la facture en PDF."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    mission = db.query(Mission).filter(Mission.id == invoice.mission_id).first()

    # Seul le freelance de la mission ou un admin peut télécharger
    if current_user.role != "admin" and mission.freelance_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    pdf_bytes = generate_invoice_pdf(invoice, mission)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={invoice.number}.pdf"},
    )


# ---------------------------------------------------------------------------
# Historique du freelance
# ---------------------------------------------------------------------------

@router.get("/me/history", response_model=list[HistoryEntry])
def get_my_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne l'historique des missions payées du freelance connecté.
    Règle d'intégrité : seules les missions avec statut 'paid' apparaissent.
    """
    missions = db.query(Mission).filter(
        Mission.freelance_id == current_user.id,
        Mission.status == "paid",
    ).order_by(Mission.paid_at.desc()).all()

    history = []
    for mission in missions:
        invoice = db.query(Invoice).filter(Invoice.mission_id == mission.id).first()
        proof = None
        if invoice:
            proof = db.query(BlockchainProof).filter(
                BlockchainProof.invoice_id == invoice.id
            ).first()
        history.append(HistoryEntry(
            mission=mission,
            invoice=invoice,
            blockchain_proof=proof,
        ))
    return history


# ---------------------------------------------------------------------------
# Journal d'audit (admin uniquement)
# ---------------------------------------------------------------------------

@router.get("/audit-logs", response_model=list[AuditLogRead])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le journal d'audit — réservé aux admins."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux admins")
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()
    return logs
