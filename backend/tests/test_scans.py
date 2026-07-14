"""Phase 1 exit criteria as executable tests."""
import io

from app.core.config import get_settings

CREDS_A = {"email": "a@example.com", "password": "password123"}
CREDS_B = {"email": "b@example.com", "password": "password123"}

# Smallest valid PNG (1x1 pixel) -- enough to exercise the pipeline.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63fcffff3f0300050201a5f6f5310000000049454e"
    "44ae426082"
)


def _register(client, creds) -> dict:
    token = client.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers, name="photo.png", mime="image/png", data=TINY_PNG):
    return client.post(
        "/scans", headers=headers, files={"file": (name, io.BytesIO(data), mime)}
    )


def test_upload_and_history(client, tmp_path):
    get_settings().upload_dir = str(tmp_path)  # keep test files out of the repo
    h = _register(client, CREDS_A)

    r = _upload(client, h)
    assert r.status_code == 201
    scan = r.json()
    assert scan["status"] == "uploaded"

    r = client.get("/scans", headers=h)
    assert r.status_code == 200
    assert len(r.json()["scans"]) == 1

    r = client.get(f"/scans/{scan['id']}/image", headers=h)
    assert r.status_code == 200
    assert r.content == TINY_PNG  # what goes in comes back out


def test_rejects_non_images(client, tmp_path):
    get_settings().upload_dir = str(tmp_path)
    h = _register(client, CREDS_A)
    r = _upload(client, h, name="report.pdf", mime="application/pdf", data=b"%PDF-fake")
    assert r.status_code == 415


def test_requires_auth(client):
    assert _upload(client, headers={}).status_code == 401


def test_user_isolation(client, tmp_path):
    """User B must never see or fetch user A's scans."""
    get_settings().upload_dir = str(tmp_path)
    h_a = _register(client, CREDS_A)
    h_b = _register(client, CREDS_B)

    scan_id = _upload(client, h_a).json()["id"]

    assert client.get("/scans", headers=h_b).json()["scans"] == []
    assert client.get(f"/scans/{scan_id}", headers=h_b).status_code == 404
    assert client.get(f"/scans/{scan_id}/image", headers=h_b).status_code == 404
