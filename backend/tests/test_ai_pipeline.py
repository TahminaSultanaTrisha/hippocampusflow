"""Phase 2 exit criteria. The AI itself is mocked (tests must be free,
fast, and runnable offline) -- what we verify is OUR pipeline: statuses,
routing, persistence, and the chat flow around the AI calls."""
import io

from app.core.config import get_settings
from app.services.ai import analysis, chat as chat_service, classifier
from app.services.ai import client as ai_client

CREDS = {"email": "ai@example.com", "password": "password123"}
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63fcffff3f0300050201a5f6f5310000000049454e"
    "44ae426082"
)


def _register(client_, creds=CREDS):
    token = client_.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload(client_, headers):
    return client_.post("/scans", headers=headers,
                        files={"file": ("p.png", io.BytesIO(TINY_PNG), "image/png")})


def test_full_pipeline_with_mocked_ai(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    monkeypatch.setattr(classifier, "classify", lambda b, e: {
        "category": "product", "confidence": 0.92,
        "observations": "A blue ceramic mug."})
    monkeypatch.setattr(ai_client, "complete_json", lambda **kw: {
        "summary": "A ceramic coffee mug, roughly 350ml.",
        "details": {"Material": "Ceramic", "Colour": "Blue"},
        "suggested_actions": ["Find similar mugs", "Save to wishlist"]})

    h = _register(client)
    scan_id = _upload(client, h).json()["id"]

    # TestClient runs background tasks before returning, so it's done already.
    r = client.get(f"/scans/{scan_id}", headers=h).json()
    assert r["status"] == "complete"
    assert r["category"] == "product"
    assert r["summary"].startswith("A ceramic")
    assert r["details"]["Material"] == "Ceramic"
    assert "Save to wishlist" in r["suggested_actions"]
    assert r["agent"] == "product"  # Phase 4: products now route to the Product agent


def test_missing_api_key_marks_scan_failed(client, tmp_path):
    get_settings().upload_dir = str(tmp_path)
    get_settings().anthropic_api_key = ""
    h = _register(client)
    scan_id = _upload(client, h).json()["id"]
    r = client.get(f"/scans/{scan_id}", headers=h).json()
    assert r["status"] == "failed"
    assert "ANTHROPIC_API_KEY" in r["summary"]


def test_chat_flow(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    monkeypatch.setattr(analysis, "run_analysis", lambda scan_id: None)
    monkeypatch.setattr(chat_service, "reply", lambda db, scan: "It looks dishwasher safe.")

    h = _register(client)
    scan_id = _upload(client, h).json()["id"]

    r = client.post(f"/scans/{scan_id}/messages", headers=h,
                    json={"content": "Is it dishwasher safe?"})
    assert r.status_code == 200
    assert r.json()["role"] == "assistant"

    msgs = client.get(f"/scans/{scan_id}/messages", headers=h).json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["content"] == "It looks dishwasher safe."


def test_empty_message_rejected(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    monkeypatch.setattr(analysis, "run_analysis", lambda scan_id: None)
    h = _register(client)
    scan_id = _upload(client, h).json()["id"]
    r = client.post(f"/scans/{scan_id}/messages", headers=h, json={"content": "   "})
    assert r.status_code == 400
