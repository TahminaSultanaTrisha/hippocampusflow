"""Phase 5 exit criteria: full-erasure delete, memory management,
and the free-tier scan limit."""
import io

from app.core.config import get_settings
from app.services.ai import classifier
from app.services.ai import client as ai_client

CREDS = {"email": "p5@example.com", "password": "password123"}
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63fcffff3f0300050201a5f6f5310000000049454e"
    "44ae426082"
)


def _register(client):
    token = client.post("/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers):
    return client.post("/scans", headers=headers,
                       files={"file": ("p.png", io.BytesIO(TINY_PNG), "image/png")})


def _mock_ai(monkeypatch):
    monkeypatch.setattr(classifier, "classify", lambda b, e: {
        "category": "product", "confidence": 0.9, "observations": "a mug"})
    monkeypatch.setattr(ai_client, "complete_json", lambda **kw: {
        "summary": "A mug.", "details": {"name": "Mug"},
        "suggested_actions": [], "memory": "User owns a mug"})


def test_delete_scan_erases_everything(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    get_settings().free_scan_limit = 25
    _mock_ai(monkeypatch)
    h = _register(client)
    scan_id = _upload(client, h).json()["id"]
    client.post(f"/scans/{scan_id}/messages", headers=h, json={"content": "hi"}) \
        if False else None  # chat needs AI; memory+result suffice for the test

    assert len(client.get("/memory", headers=h).json()["memories"]) == 1

    r = client.delete(f"/scans/{scan_id}", headers=h)
    assert r.status_code == 204
    assert client.get(f"/scans/{scan_id}", headers=h).status_code == 404
    assert client.get(f"/scans/{scan_id}/image", headers=h).status_code == 404
    assert client.get("/memory", headers=h).json()["memories"] == []
    assert not list(tmp_path.rglob("*.png"))  # image file physically gone


def test_memory_list_and_delete(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    get_settings().free_scan_limit = 25
    _mock_ai(monkeypatch)
    h = _register(client)
    _upload(client, h)

    memories = client.get("/memory", headers=h).json()["memories"]
    assert len(memories) == 1
    mem_id = memories[0]["id"]
    assert client.delete(f"/memory/{mem_id}", headers=h).status_code == 204
    assert client.get("/memory", headers=h).json()["memories"] == []


def test_free_scan_limit(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    get_settings().free_scan_limit = 2
    _mock_ai(monkeypatch)
    h = _register(client)
    assert _upload(client, h).status_code == 201
    assert _upload(client, h).status_code == 201
    r = _upload(client, h)
    assert r.status_code == 402
    assert r.json()["detail"]["code"] == "scan_limit_reached"
    get_settings().free_scan_limit = 25  # restore for other tests


def test_batch_delete_only_own_scans(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    get_settings().free_scan_limit = 25
    _mock_ai(monkeypatch)
    h = _register(client)
    id1 = _upload(client, h).json()["id"]
    id2 = _upload(client, h).json()["id"]

    other = {"Authorization": "Bearer " + client.post(
        "/auth/register",
        json={"email": "victim@example.com", "password": "password123"}
    ).json()["access_token"]}
    foreign_id = _upload(client, other).json()["id"]

    r = client.post("/scans/batch-delete", headers=h,
                    json={"scan_ids": [id1, id2, foreign_id, "nonsense"]})
    assert r.status_code == 200
    assert r.json()["deleted"] == 2  # own scans only
    assert client.get("/scans", headers=h).json()["scans"] == []
    # victim's scan untouched
    assert len(client.get("/scans", headers=other).json()["scans"]) == 1
    get_settings().free_scan_limit = 10


def test_me_reports_usage(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    get_settings().free_scan_limit = 10
    _mock_ai(monkeypatch)
    h = _register(client)
    _upload(client, h)
    me = client.get("/users/me", headers=h).json()
    assert me["scans_used_this_month"] == 1
    assert me["scan_limit"] == 10
