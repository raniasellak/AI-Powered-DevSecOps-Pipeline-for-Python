
def test_admin_endpoint_requires_authentication(client):
    response = client.get("/auth/admin/ping")

    assert response.status_code == 401


def test_freelance_cannot_access_admin_endpoint(client):
    client.post(
        "/auth/register",
        json={
            "email": "freelance@example.com",
            "password": "StrongPassword123!",
            "role": "freelance",
        },
    )

    login = client.post(
        "/auth/login",
        data={
            "username": "freelance@example.com",
            "password": "StrongPassword123!",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
