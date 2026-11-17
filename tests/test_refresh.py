
from tests.test_auth import login_user, register_user


def test_refresh_token_rotation(client):
    register_user(client)
    login = login_user(client)

    old_refresh = login.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )

    assert response.status_code == 200

    new_refresh = response.json()["refresh_token"]

    assert new_refresh != old_refresh
    assert response.json()["access_token"]


def test_old_refresh_token_reuse_is_rejected(client):
    register_user(client)
    login = login_user(client)

    old_refresh = login.json()["refresh_token"]

    rotated = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )

    assert rotated.status_code == 200

    new_refresh = rotated.json()["refresh_token"]

    # Rejouer l'ancien jeton doit invalider toute la famille.
    replay = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )

    assert replay.status_code == 401

    # Le nouveau jeton de cette famille doit également être refusé.
    reuse = client.post(
        "/auth/refresh",
        json={"refresh_token": new_refresh},
    )

    assert reuse.status_code == 401


def test_unknown_refresh_token_rejected(client):
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "unknown-token-value-123456"},
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    register_user(client)
    login = login_user(client)

    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout.status_code == 204

    refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh.status_code == 401
