from datetime import datetime, timedelta, timezone

from backend.app.invoices.utils import (
    GENESIS_HASH,
    amount_matches,
    compute_audit_hash,
    generate_token,
    hash_token,
    link_is_usable,
    verify_chain,
)


def test_facture_differente_de_la_mission_refusee():
    assert amount_matches(100000, 100000) is True
    assert amount_matches(100001, 100000) is False
    assert amount_matches(99999, 100000) is False


def test_lien_expire_refuse():
    passe = datetime.now(timezone.utc) - timedelta(hours=1)
    assert link_is_usable(passe, max_uses=1, used_count=0) is False


def test_lien_deja_utilise_refuse():
    futur = datetime.now(timezone.utc) + timedelta(hours=1)
    assert link_is_usable(futur, max_uses=1, used_count=1) is False


def test_lien_valide_accepte():
    futur = datetime.now(timezone.utc) + timedelta(hours=1)
    assert link_is_usable(futur, max_uses=1, used_count=0) is True


def test_token_imprevisible_et_hash_stable():
    assert generate_token() != generate_token()
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != "abc"


def _chaine():
    h1 = compute_audit_hash(GENESIS_HASH, "invoice_created", {"id": 1})
    h2 = compute_audit_hash(h1, "link_created", {"id": 1})
    ligne1 = {
        "prev_hash": GENESIS_HASH,
        "event": "invoice_created",
        "payload": {"id": 1},
        "hash": h1,
    }
    ligne2 = {
        "prev_hash": h1,
        "event": "link_created",
        "payload": {"id": 1},
        "hash": h2,
    }
    return [ligne1, ligne2]


def test_chaine_audit_valide():
    assert verify_chain(_chaine()) is True


def test_chaine_audit_modifiee_detectee():
    chaine = _chaine()
    chaine[0]["payload"] = {"id": 999}  # quelqu'un triche
    assert verify_chain(chaine) is False