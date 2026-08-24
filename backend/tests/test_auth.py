from tests.conftest import register_and_login


def test_register_creates_resident(client):
    resp = client.post("/auth/register", json={
        "name": "Jane Doe", "email": "jane@test.dev", "password": "StrongPass123!",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["role"] == "resident"
    assert "access_token" in body


def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={"name": "Jane", "email": "dup@test.dev", "password": "StrongPass123!"})
    resp = client.post("/auth/register", json={"name": "Jane 2", "email": "dup@test.dev", "password": "StrongPass123!"})
    assert resp.status_code == 409


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"name": "Jane", "email": "wrong@test.dev", "password": "StrongPass123!"})
    resp = client.post("/auth/login", json={"email": "wrong@test.dev", "password": "WrongPassword!"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    token = register_and_login(client)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "resident@test.dev"
