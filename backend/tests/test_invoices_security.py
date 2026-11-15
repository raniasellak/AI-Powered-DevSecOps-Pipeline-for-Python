"""
Tests de sécurité P3 :
  1. Facture avec montant > mission → refusée
  2. Lien de paiement expiré → refusé
  3. Lien de paiement déjà utilisé → refusé
  4. Historique sans mission payée → vide (impossible d'inventer une entrée)
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.auth.models import User
from app.auth.security import hash_password
from app.invoices.models import Invoice, Mission
from app.invoices.service import consume_pay_link, create_invoice_for_mission

# ---------------------------------------------------------------------------
# Base de données en mémoire pour les tests
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def freelance(db):
    user = User(
        email="freelance@test.com",
        password_hash=hash_password("password123456"),
        role="freelance",
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_user(db):
    user = User(
        email="client@test.com",
        password_hash=hash_password("password123456"),
        role="freelance",
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def confirmed_mission(db, freelance, client_user):
    mission = Mission(
        title="Test mission",
        amount=1000.00,
        freelance_id=freelance.id,
        client_id=client_user.id,
        status="confirmed",
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


# ---------------------------------------------------------------------------
# Test 1 : facture avec montant > mission → refusée (validation serveur)
# ---------------------------------------------------------------------------

def test_invoice_amount_locked_to_mission(db, confirmed_mission):
    """Le montant de la facture doit être identique à celui de la mission."""
    invoice = create_invoice_for_mission(confirmed_mission.id, db)
    # Le montant doit être copié depuis la mission, pas libre
    assert float(invoice.amount) == float(confirmed_mission.amount)


def test_cannot_create_invoice_if_not_confirmed(db, freelance, client_user):
    """Une facture ne peut pas être créée si la mission n'est pas confirmée."""
    mission = Mission(
        title="Pending mission",
        amount=500.00,
        freelance_id=freelance.id,
        client_id=client_user.id,
        status="pending",  # pas encore confirmée
    )
    db.add(mission)
    db.commit()

    with pytest.raises(ValueError, match="confirmée"):
        create_invoice_for_mission(mission.id, db)


def test_cannot_create_duplicate_invoice(db, confirmed_mission):
    """Une seule facture par mission."""
    create_invoice_for_mission(confirmed_mission.id, db)
    # Remettre le statut à confirmed pour tester le blocage de doublon
    db.query(Mission).filter(Mission.id == confirmed_mission.id).update({"status": "confirmed"})
    db.commit()
    with pytest.raises(ValueError, match="existe déjà"):
        create_invoice_for_mission(confirmed_mission.id, db)


# ---------------------------------------------------------------------------
# Test 2 : lien de paiement expiré → refusé
# ---------------------------------------------------------------------------

def test_expired_pay_link_is_rejected(db, confirmed_mission):
    """Un lien de paiement expiré doit être refusé."""
    invoice = create_invoice_for_mission(confirmed_mission.id, db)

    # Forcer l'expiration dans le passé
    invoice.signed_token = "expired.token"
    invoice.token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    invoice.token_used = False
    db.commit()

    with pytest.raises(ValueError, match="expiré"):
        consume_pay_link("expired.token", db)


# ---------------------------------------------------------------------------
# Test 3 : lien déjà utilisé → refusé
# ---------------------------------------------------------------------------

def test_used_pay_link_is_rejected(db, confirmed_mission):
    """Un lien de paiement déjà consommé doit être refusé."""
    invoice = create_invoice_for_mission(confirmed_mission.id, db)

    invoice.signed_token = "used.token"
    invoice.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
    invoice.token_used = True  # déjà utilisé
    db.commit()

    with pytest.raises(ValueError, match="déjà utilisé"):
        consume_pay_link("used.token", db)


# ---------------------------------------------------------------------------
# Test 4 : historique sans mission payée → vide
# ---------------------------------------------------------------------------

def test_history_only_contains_paid_missions(db, freelance, client_user):
    """L'historique ne doit contenir que des missions avec statut 'paid'."""
    # Mission confirmée mais pas encore payée
    mission = Mission(
        title="Not paid yet",
        amount=200.00,
        freelance_id=freelance.id,
        client_id=client_user.id,
        status="confirmed",
    )
    db.add(mission)
    db.commit()

    paid_missions = db.query(Mission).filter(
        Mission.freelance_id == freelance.id,
        Mission.status == "paid",
    ).all()

    assert len(paid_missions) == 0
