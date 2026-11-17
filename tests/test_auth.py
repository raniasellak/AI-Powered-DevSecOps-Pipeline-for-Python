
def register_user(client, email="test@example.com"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "role": "freelance",
        },
    )


def login_user(client, email="test@example.com"):
    return client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "StrongPassword123!",
        },
    )


def test_register_success(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "password_hash" not in response.json()


def test_duplicate_email_rejected(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 409


def test_admin_registration_forbidden(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_short_password_rejected(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_success(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_wrong_password_rejected(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_unknown_user_rejected(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_valid_token(client):
    register_user(client)
    login_response = login_user(client)

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
