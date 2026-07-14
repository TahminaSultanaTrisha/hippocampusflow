"""Phase 3 exit criteria: memories are created, retrieved into analysis,
searchable, and the ask endpoint works. AI mocked throughout."""
import io

from app.core.config import get_settings
from app.services import memory_service
from app.services.ai import classifier
from app.services.ai import client as ai_client

CREDS = {"email": "mem@example.com", "password": "password123"}
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


def _mock_ai(monkeypatch, memory_sentence, captured=None):
    monkeypatch.setattr(classifier, "classify", lambda b, e: {
        "category": "product", "confidence": 0.9,
        "observations": "A blue ceramic mug with a handle."})

    def fake_complete_json(**kw):
        if captured is not None:
            captured.append(kw)
        return {"summary": "A blue ceramic mug.", "details": {},
                "suggested_actions": [], "memory": memory_sentence}
    monkeypatch.setattr(ai_client, "complete_json", fake_complete_json)


def test_memory_stored_and_searchable(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    _mock_ai(monkeypatch, "User owns a blue ceramic mug")
    h = _register(client)
    _upload(client, h)

    r = client.get("/memory/search", params={"q": "ceramic mug"}, headers=h)
    assert r.status_code == 200
    assert len(r.json()["scans"]) == 1


def test_second_scan_sees_first_scans_memory(client, tmp_path, monkeypatch):
    """The heart of Phase 3: analysis N+1 receives memory from analysis N."""
    get_settings().upload_dir = str(tmp_path)
    captured: list[dict] = []
    _mock_ai(monkeypatch, "User owns a blue ceramic mug", captured)

    h = _register(client)
    _upload(client, h)   # first scan -> creates the memory
    _upload(client, h)   # second scan -> should receive it as context

    second_call_text = captured[1]["content"][1]["text"]
    assert "blue ceramic mug" in second_call_text
    assert "remember" in second_call_text.lower()


def test_memory_ask(client, tmp_path, monkeypatch):
    get_settings().upload_dir = str(tmp_path)
    _mock_ai(monkeypatch, "User owns a blue ceramic mug")
    monkeypatch.setattr(memory_service, "ask",
                        lambda db, uid, q: "You scanned a blue ceramic mug.")
    h = _register(client)
    _upload(client, h)

    r = client.post("/memory/ask", json={"question": "what mug do I have?"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "mug" in body["answer"]
    assert len(body["scans"]) == 1


def test_ask_requires_auth(client):
    assert client.post("/memory/ask", json={"question": "hi"}).status_code == 401
