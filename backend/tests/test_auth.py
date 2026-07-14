"""Phase 0 exit criteria as executable tests."""

CREDS = {"email": "ada@example.com", "password": "supersecret1", "display_name": "Ada"}


def test_register_login_and_me(client):
    # Register returns tokens
    r = client.post("/auth/register", json=CREDS)
    assert r.status_code == 201
    tokens = r.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    # Login works with the same credentials
    r = client.post("/auth/login", json={"email": CREDS["email"], "password": CREDS["password"]})
    assert r.status_code == 200
    access = r.json()["access_token"]

    # Protected route works with the token...
    r = client.get("/users/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == CREDS["email"]
    assert "password_hash" not in body  # schema filtering works

    # ...and fails without it
    assert client.get("/users/me").status_code == 401


def test_duplicate_email_rejected(client):
    assert client.post("/auth/register", json=CREDS).status_code == 201
    assert client.post("/auth/register", json=CREDS).status_code == 409


def test_wrong_password_rejected(client):
    client.post("/auth/register", json=CREDS)
    r = client.post("/auth/login", json={"email": CREDS["email"], "password": "wrongwrong1"})
    assert r.status_code == 401


def test_refresh_flow(client):
    refresh_token = client.post("/auth/register", json=CREDS).json()["refresh_token"]
    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()

    # A refresh token must NOT work as an access token
    r = client.get("/users/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "b@example.com", "password": "short"})
    assert r.status_code == 422  # Pydantic validation, before our code runs
